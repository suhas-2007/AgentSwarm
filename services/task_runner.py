import json
import traceback

from sqlalchemy import select

from database.connection import SessionLocal
from database.models import Task

from graph.workflow import app as workflow_app

from services.task_control import TaskStopped


def sync_task_from_state(
    task: Task,
    state: dict,
    db
):

    # Never overwrite a STOPPED task with
    # a late LangGraph state update.
    if task.status == "STOPPED":

        db.refresh(task)

        return

    task.status = state.get(
        "status",
        task.status
    )

    task.plan = state.get(
        "plan",
        task.plan
    )

    task.research = state.get(
        "research",
        task.research
    )

    task.content = state.get(
        "content",
        task.content
    )

    task.code = state.get(
        "code",
        task.code
    )

    task.evaluation = state.get(
        "evaluation",
        task.evaluation
    )

    task.final_answer = state.get(
        "final_answer",
        task.final_answer
    )

    task.revision_count = state.get(
        "revision_count",
        task.revision_count
    )

    task.current_task_id = state.get(
        "current_task_id",
        task.current_task_id
    )

    completed_tasks = state.get(
        "completed_tasks"
    )

    if completed_tasks is not None:

        task.completed_tasks = json.dumps(
            completed_tasks
        )

    db.commit()

    db.refresh(task)


def run_task(
    task_id: int
):

    print(
        f"[TASK RUNNER] Starting task {task_id}"
    )

    db = SessionLocal()

    try:

        print(
            f"[TASK RUNNER] Loading task {task_id}"
        )

        task = db.scalar(
            select(Task).where(
                Task.id == task_id
            )
        )

        if task is None:

            print(
                f"[TASK RUNNER] Task {task_id} "
                "was not found."
            )

            return

        print(
            f"[TASK RUNNER] Task {task_id} "
            f"current status: {task.status}"
        )

        # The user may have stopped the task
        # before the background task started.
        if task.status == "STOPPED":

            print(
                f"[TASK RUNNER] Task {task_id} "
                "was already stopped."
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
            "status changed to RUNNING."
        )

        print(
            f"[TASK RUNNER] Invoking LangGraph "
            f"for task {task_id}..."
        )

        try:

            result = workflow_app.invoke(
                initial_state,
                config
            )

            print(
                f"[TASK RUNNER] LangGraph completed "
                f"for task {task_id}."
            )

            print(
                f"[TASK RUNNER] Final workflow state: "
                f"{result}"
            )

        except TaskStopped:

            print(
                f"[TASK RUNNER] Task {task_id} "
                "was stopped."
            )

            task = db.scalar(
                select(Task).where(
                    Task.id == task_id
                )
            )

            if task is not None:

                task.status = "STOPPED"

                task.current_task_id = None

                db.commit()

            return

        except Exception as error:

            print(
                f"[TASK RUNNER] ERROR while running "
                f"task {task_id}: {error}"
            )

            traceback.print_exc()

            task = db.scalar(
                select(Task).where(
                    Task.id == task_id
                )
            )

            if task is not None:

                if task.status != "STOPPED":

                    task.status = "FAILED"

                    db.commit()

            return

        sync_task_from_state(
            task,
            result,
            db
        )

        print(
            f"[TASK RUNNER] Task {task_id} "
            "state synchronized to database."
        )

    except TaskStopped:

        print(
            f"[TASK RUNNER] Task {task_id} "
            "was stopped."
        )

        task = db.scalar(
            select(Task).where(
                Task.id == task_id
            )
        )

        if task is not None:

            task.status = "STOPPED"

            task.current_task_id = None

            db.commit()

    except Exception as error:

        print(
            f"[TASK RUNNER] UNEXPECTED ERROR "
            f"for task {task_id}: {error}"
        )

        traceback.print_exc()

        task = db.scalar(
            select(Task).where(
                Task.id == task_id
            )
        )

        if task is not None:

            # Do not turn a user-stopped task
            # into FAILED because of a late exception.
            if task.status != "STOPPED":

                task.status = "FAILED"

                db.commit()

    finally:

        print(
            f"[TASK RUNNER] Closing database "
            f"connection for task {task_id}."
        )

        db.close()