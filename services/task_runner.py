import json
import traceback

from sqlalchemy import select, update

from database.connection import SessionLocal
from database.models import Task

from graph.workflow import app as workflow_app

from services.task_control import TaskStopped


def sync_task_from_state(
    task: Task,
    state: dict,
    db
):

    values = {
        "status": state.get(
            "status",
            task.status
        ),

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

    # If the task was stopped by the user
    # before this synchronization committed,
    # the conditional UPDATE affects zero rows.
    # STOPPED therefore remains authoritative.
    if result.rowcount == 0:

        db.refresh(task)

        return


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

        # Never overwrite a task that the
        # user has explicitly stopped.
        if task.status == "STOPPED":

            return

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

        # The user may have stopped the task
        # before the background task started.
        if task.status == "STOPPED":

            print(
                f"[TASK RUNNER] Task {task_id} "
                "was already stopped.",
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

        config = {
            "configurable": {
                "thread_id":
                    str(task.id)
            }
        }

        task.status = "RUNNING"

        db.commit()

        print(
            f"[TASK RUNNER] Task {task_id} "
            "status changed to RUNNING.",
            flush=True
        )

        print(
            f"[TASK RUNNER] Invoking LangGraph "
            f"for task {task_id}...",
            flush=True
        )

        try:

            result = workflow_app.invoke(
                initial_state,
                config
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