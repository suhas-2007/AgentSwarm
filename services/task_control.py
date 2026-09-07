from sqlalchemy import select

from database.connection import SessionLocal
from database.models import Task


class TaskStopped(Exception):
    """
    Raised when a task has been stopped by the user.
    """

    pass


def check_task_stopped(
    task_id: int
) -> None:

    db = SessionLocal()

    try:

        task = db.scalar(
            select(Task).where(
                Task.id == task_id
            )
        )

        if task is not None and task.status == "STOPPED":

            raise TaskStopped(
                f"Task {task_id} was stopped by the user."
            )

    finally:

        db.close()