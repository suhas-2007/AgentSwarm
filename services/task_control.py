from sqlalchemy import select

from database.connection import SessionLocal
from database.models import Task


class TaskStopped(Exception):
    # raised when user stops a task
    pass


# all valid task statuses

VALID_TASK_STATUSES = {
    "STARTING",
    "RUNNING",
    "PLANNING",
    "RESEARCHING",
    "CODING",
    "CREATING_CONTENT",
    "EVALUATING",
    "REVISING",
    "WAITING_FOR_HUMAN",
    "EVALUATION_UNAVAILABLE",
    "FINALIZING",
    "COMPLETED",
    "FAILED",
    "STOPPED"
}


TERMINAL_TASK_STATUSES = {
    "COMPLETED",
    "FAILED",
    "STOPPED"
}


ALLOWED_STATUS_TRANSITIONS = {
    "STARTING": {
        "RUNNING",
        "STOPPED",
        "FAILED"
    },

    "RUNNING": {
        "PLANNING",
        "RESEARCHING",
        "CODING",
        "CREATING_CONTENT",
        "EVALUATING",
        "REVISING",
        "WAITING_FOR_HUMAN",
        "EVALUATION_UNAVAILABLE",
        "FINALIZING",
        "COMPLETED",
        "FAILED",
        "STOPPED"
    },

    "PLANNING": {
        "RESEARCHING",
        "CODING",
        "CREATING_CONTENT",
        "EVALUATING",
        "FAILED",
        "STOPPED"
    },

    "RESEARCHING": {
        "PLANNING",
        "RESEARCHING",
        "CODING",
        "CREATING_CONTENT",
        "EVALUATING",
        "REVISING",
        "FAILED",
        "STOPPED"
    },

    "CODING": {
        "PLANNING",
        "RESEARCHING",
        "CODING",
        "CREATING_CONTENT",
        "EVALUATING",
        "REVISING",
        "FAILED",
        "STOPPED"
    },

    "CREATING_CONTENT": {
        "PLANNING",
        "RESEARCHING",
        "CODING",
        "CREATING_CONTENT",
        "EVALUATING",
        "REVISING",
        "FAILED",
        "STOPPED"
    },

    "EVALUATING": {
        "REVISING",
        "WAITING_FOR_HUMAN",
        "EVALUATION_UNAVAILABLE",
        "FAILED",
        "STOPPED"
    },

    "REVISING": {
        "RESEARCHING",
        "CODING",
        "CREATING_CONTENT",
        "EVALUATING",
        "FAILED",
        "STOPPED"
    },

    "WAITING_FOR_HUMAN": {
        "REVISING",
        "FINALIZING",
        "FAILED",
        "STOPPED"
    },

    "EVALUATION_UNAVAILABLE": {
        "STOPPED",
        "FAILED"
    },

    "FINALIZING": {
        "COMPLETED",
        "FAILED",
        "STOPPED"
    },

    "COMPLETED": set(),

    "FAILED": set(),

    "STOPPED": set()
}


def validate_task_status(
    status: str
) -> None:
    # make sure status is valid

    if status not in VALID_TASK_STATUSES:

        raise ValueError(
            f"Invalid task status: {status}"
        )


def validate_status_transition(
    current_status: str,
    new_status: str
) -> None:
    # check if transition between statuses is allowed

    validate_task_status(
        current_status
    )

    validate_task_status(
        new_status
    )

    if current_status == new_status:

        return

    allowed_statuses = (
        ALLOWED_STATUS_TRANSITIONS[
            current_status
        ]
    )

    if new_status not in allowed_statuses:

        raise ValueError(
            f"Invalid task status transition: "
            f"{current_status} -> {new_status}"
        )


def is_terminal_status(
    status: str
) -> bool:
    # returns True if task is finished/stopped/failed

    validate_task_status(
        status
    )

    return status in TERMINAL_TASK_STATUSES


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

        if (
            task is not None
            and task.status == "STOPPED"
        ):

            raise TaskStopped(
                f"Task {task_id} was stopped "
                "by the user."
            )

    finally:

        db.close()