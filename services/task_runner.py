import json
import time
import traceback

from sqlalchemy import select, update

from database.connection import SessionLocal
from database.models import Task

from graph.workflow import app as workflow_app

from services.task_control import (
    TaskStopped,
    validate_status_transition
)


MAX_ATTEMPTS = 3
RETRY_DELAYS = [2, 4]


def is_retryable_error(
    error: Exception
) -> bool:
    """
    Determine whether an exception is likely
    to be caused by a temporary external
    service or network problem.
    """

    error_text = str(error).lower()

    retryable_terms = [
        "timeout",
        "timed out",
        "connection",
        "connecterror",
        "connectionerror",
        "connection reset",
        "temporarily unavailable",
        "service unavailable",
        "server error",
        "internal server error",
        "rate limit",
        "rate_limit",
        "too many requests",
        "resource exhausted",
        "resource_exhausted",
        "429",
        "502",
        "503",
        "504",
        "unavailable"
    ]

    return any(
        term in error_text
        for term in retryable_terms
    )


def sync_task_from_state(
    task: Task,
    state: dict,
    db
):
    """
    Synchronize the persisted task with the latest
    LangGraph checkpoint state.

    Checkpoint states may skip intermediate lifecycle
    statuses, so transition validation is intentionally
    not performed here.

    The database condition protects STOPPED tasks from
    being overwritten by an older or concurrent worker.
    """

    new_status = state.get(
        "status",
        task.status
    )

    values = {
        "status":
            new_status,

        "plan": state.get(
            "plan",
            task.plan
        ),

        "research": state.get(
            "research",
            task.research
        ),

        "content": state.get(
            "content",
            task.content
        ),

        "code": state.get(
            "code",
            task.code
        ),

        "evaluation": state.get(
            "evaluation",
            task.evaluation
        ),

        "final_answer": state.get(
            "final_answer",
            task.final_answer
        ),

        "revision_count": state.get(
            "revision_count",
            task.revision_count
        ),

        "current_task_id": state.get(
            "current_task_id",
            task.current_task_id
        )
    }

    completed_tasks = state.get(
        "completed_tasks"
    )

    if completed_tasks is not None:

        values["completed_tasks"] = (
            json.dumps(
                completed_tasks
            )
        )

    result = db.execute(
        update(Task)
        .where(
            Task.id == task.id,
            Task.status != "STOPPED"
        )
        .values(**values)
    )

    db.commit()

    db.refresh(task)

    if result.rowcount == 0:

        db.refresh(task)

        return


def claim_task(
    task_id: int,
    db
) -> bool:
    """
    Atomically claim a newly created task.

    Only STARTING tasks can be claimed.
    """

    validate_status_transition(
        "STARTING",
        "RUNNING"
    )

    result = db.execute(
        update(Task)
        .where(
            Task.id == task_id,
            Task.status == "STARTING"
        )
        .values(
            status="RUNNING"
        )
    )

    db.commit()

    return result.rowcount == 1


def get_checkpoint_state(
    config: dict
):
    """
    Read the latest LangGraph checkpoint.
    """

    try:

        snapshot = workflow_app.get_state(
            config
        )

    except Exception as error:

        print(
            "[TASK RUNNER] Could not load "
            f"LangGraph checkpoint: {error}",
            flush=True
        )

        return None

    if snapshot is None:

        return None

    if not snapshot.values:

        return None

    return snapshot.values


def mark_task_failed(
    task_id: int,
    db
):

    try:

        db.rollback()

        task = db.scalar(
            select(Task).where(
                Task.id == task_id
            )
        )

        if task is None:

            return

        if task.status == "STOPPED":

            return

        if task.status == "FAILED":

            return

        validate_status_transition(
            task.status,
            "FAILED"
        )

        task.status = "FAILED"

        task.current_task_id = None

        db.commit()

        db.refresh(task)

    except Exception as recovery_error:

        db.rollback()

        print(
            f"[TASK RUNNER] Could not mark "
            f"task {task_id} as FAILED: "
            f"{recovery_error}",
            flush=True
        )


def mark_task_stopped(
    task_id: int,
    db
):

    try:

        db.rollback()

        task = db.scalar(
            select(Task).where(
                Task.id == task_id
            )
        )

        if task is None:

            return

        if task.status == "STOPPED":

            return

        if task.status == "COMPLETED":

            return

        if task.status == "FAILED":

            return

        validate_status_transition(
            task.status,
            "STOPPED"
        )

        task.status = "STOPPED"

        task.current_task_id = None

        db.commit()

        db.refresh(task)

    except Exception as recovery_error:

        db.rollback()

        print(
            f"[TASK RUNNER] Could not mark "
            f"task {task_id} as STOPPED: "
            f"{recovery_error}",
            flush=True
        )


def run_workflow_with_retry(
    initial_state: dict | None,
    config: dict,
    task_id: int,
    resume: bool = False
):
    """
    Execute LangGraph with limited retries for
    temporary external-service failures.
    """

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1
    ):

        try:

            print(
                f"[TASK RUNNER] Workflow attempt "
                f"{attempt}/{MAX_ATTEMPTS} "
                f"for task {task_id}.",
                flush=True
            )

            if resume:

                print(
                    f"[TASK RUNNER] Resuming task "
                    f"{task_id} from LangGraph "
                    "checkpoint.",
                    flush=True
                )

                return workflow_app.invoke(
                    None,
                    config
                )

            return workflow_app.invoke(
                initial_state,
                config
            )

        except TaskStopped:

            raise

        except Exception as error:

            retryable = is_retryable_error(
                error
            )

            if (
                not retryable
                or attempt >= MAX_ATTEMPTS
            ):

                raise

            delay = RETRY_DELAYS[
                attempt - 1
            ]

            print(
                f"[TASK RUNNER] Temporary error "
                f"for task {task_id}. "
                f"Retrying in {delay}s...",
                flush=True
            )

            time.sleep(
                delay
            )

    raise RuntimeError(
        "Workflow retry loop exited unexpectedly."
    )


def run_task(
    task_id: int
):

    print(
        f"[TASK RUNNER] Starting task {task_id}",
        flush=True
    )

    db = SessionLocal()

    try:

        print(
            f"[TASK RUNNER] Loading task {task_id}",
            flush=True
        )

        task = db.scalar(
            select(Task).where(
                Task.id == task_id
            )
        )

        if task is None:

            print(
                f"[TASK RUNNER] Task {task_id} "
                "was not found.",
                flush=True
            )

            return

        print(
            f"[TASK RUNNER] Task {task_id} "
            f"current status: {task.status}",
            flush=True
        )

        if task.status == "STOPPED":

            print(
                f"[TASK RUNNER] Task {task_id} "
                "was already stopped.",
                flush=True
            )

            return

        config = {
            "configurable": {
                "thread_id":
                    str(task.id)
            }
        }

        checkpoint_state = (
            get_checkpoint_state(
                config
            )
        )

        has_checkpoint = (
            checkpoint_state is not None
        )

        if task.status == "STARTING":

            claimed = claim_task(
                task_id,
                db
            )

            if not claimed:

                db.refresh(task)

                print(
                    f"[TASK RUNNER] Task {task_id} "
                    f"could not be claimed. "
                    f"Current status: {task.status}.",
                    flush=True
                )

                return

            db.refresh(task)

            print(
                f"[TASK RUNNER] Task {task_id} "
                "claimed successfully.",
                flush=True
            )

        elif task.status == "RUNNING":

            if has_checkpoint:

                print(
                    f"[TASK RUNNER] Existing checkpoint "
                    f"found for task {task_id}. "
                    "Workflow will resume.",
                    flush=True
                )

            else:

                print(
                    f"[TASK RUNNER] Task {task_id} "
                    "is RUNNING but has no checkpoint. "
                    "Starting a fresh workflow.",
                    flush=True
                )

        else:

            print(
                f"[TASK RUNNER] Task {task_id} "
                f"has status {task.status}. "
                "No workflow execution required.",
                flush=True
            )

            return

        initial_state = {

            "task_id":
                task.id,

            "user_goal":
                task.goal,

            "plan":
                "",

            "plan_tasks":
                [],

            "current_task_id":
                None,

            "completed_tasks":
                [],

            "research":
                "",

            "code":
                "",

            "content":
                "",

            "evaluation":
                "",

            "final_answer":
                "",

            "revision_count":
                0,

            "human_approval":
                "",

            "human_feedback":
                "",

            "revision_reason":
                "INITIAL",

            "status":
                "STARTING"
        }

        print(
            f"[TASK RUNNER] Task {task_id} "
            "status is RUNNING.",
            flush=True
        )

        print(
            f"[TASK RUNNER] Invoking LangGraph "
            f"for task {task_id}...",
            flush=True
        )

        try:

            result = run_workflow_with_retry(
                initial_state=(
                    None
                    if has_checkpoint
                    else initial_state
                ),
                config=config,
                task_id=task_id,
                resume=has_checkpoint
            )

            print(
                f"[TASK RUNNER] LangGraph completed "
                f"for task {task_id}.",
                flush=True
            )

        except TaskStopped:

            print(
                f"[TASK RUNNER] Task {task_id} "
                "was stopped.",
                flush=True
            )

            mark_task_stopped(
                task_id,
                db
            )

            return

        except Exception as error:

            print(
                f"[TASK RUNNER] ERROR while running "
                f"task {task_id}: {error}",
                flush=True
            )

            traceback.print_exc()

            mark_task_failed(
                task_id,
                db
            )

            return

        sync_task_from_state(
            task,
            result,
            db
        )

        print(
            f"[TASK RUNNER] Task {task_id} "
            "state synchronized to database.",
            flush=True
        )

        print(
            f"[TASK RUNNER] Task {task_id} "
            f"final status: {task.status}",
            flush=True
        )

    except TaskStopped:

        print(
            f"[TASK RUNNER] Task {task_id} "
            "was stopped.",
            flush=True
        )

        mark_task_stopped(
            task_id,
            db
        )

    except Exception as error:

        print(
            f"[TASK RUNNER] UNEXPECTED ERROR "
            f"for task {task_id}: {error}",
            flush=True
        )

        traceback.print_exc()

        mark_task_failed(
            task_id,
            db
        )

    finally:

        print(
            f"[TASK RUNNER] Closing database "
            f"connection for task {task_id}.",
            flush=True
        )

        db.close()