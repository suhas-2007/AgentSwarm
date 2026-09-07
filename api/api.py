import json
import secrets

from dotenv import load_dotenv

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    status
)

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import FileResponse

from langgraph.types import Command

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.schemas import (
    TaskRequest,
    ApprovalRequest
)

from artifacts.manager import (
    get_artifact_path,
    list_artifacts,
    delete_task_artifacts
)

from auth.dependencies import get_current_user
from auth.routes import router as auth_router

from database.connection import get_db
from database.models import (
    User,
    Task,
    TaskShare
)

from graph.workflow import app as workflow_app

from services.task_runner import run_task


load_dotenv()


app = FastAPI(
    title="AgentSwarm API",
    description="Multi-Agent Task Orchestration Engine",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    auth_router
)


# ============================================================
# BACKGROUND TASK WRAPPER
# ============================================================

def run_task_background(
    task_id: int
):

    print(
        f"[API BACKGROUND] Starting "
        f"background task for task {task_id}",
        flush=True
    )

    try:

        run_task(
            task_id
        )

        print(
            f"[API BACKGROUND] run_task() "
            f"returned for task {task_id}",
            flush=True
        )

    except Exception as error:

        print(
            f"[API BACKGROUND] ERROR while "
            f"starting task {task_id}: {error}",
            flush=True
        )

        raise


# ============================================================
# DATABASE <-> LANGGRAPH SYNCHRONIZATION
# ============================================================

def sync_task_from_state(
    task: Task,
    state: dict,
    db: Session
):

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


def get_completed_tasks(
    task: Task
) -> list[int]:

    if not task.completed_tasks:

        return []

    try:

        completed_tasks = json.loads(
            task.completed_tasks
        )

    except json.JSONDecodeError:

        return []

    if not isinstance(
        completed_tasks,
        list
    ):

        return []

    return [
        int(task_id)
        for task_id in completed_tasks
    ]


def task_response(
    task: Task
) -> dict:

    return {
        "task_id": task.id,

        "status": task.status,

        "goal": task.goal,

        "plan": task.plan,

        "research": task.research,

        "content": task.content,

        "code": task.code,

        "evaluation": task.evaluation,

        "final_answer": task.final_answer,

        "revision_count":
            task.revision_count,

        "current_task_id":
            task.current_task_id,

        "completed_tasks":
            get_completed_tasks(task)
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "service": "AgentSwarm"
    }


# ============================================================
# CREATE TASK
# ============================================================

@app.post("/tasks")
def create_task(
    request: TaskRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    task = Task(
        user_id=current_user.id,
        goal=request.goal,
        status="STARTING",
        current_task_id=None,
        completed_tasks="[]"
    )

    db.add(task)

    db.commit()

    db.refresh(task)

    task_id = task.id

    print(
        f"[API] Created task {task_id}",
        flush=True
    )

    print(
        f"[API] Scheduling background "
        f"execution for task {task_id}",
        flush=True
    )

    background_tasks.add_task(
        run_task_background,
        task_id
    )

    print(
        f"[API] Background task scheduled "
        f"for task {task_id}",
        flush=True
    )

    return task_response(task)


# ============================================================
# GET ALL TASKS
# ============================================================

@app.get("/tasks")
def get_tasks(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    tasks = db.scalars(
        select(Task)
        .where(
            Task.user_id ==
                current_user.id
        )
        .order_by(
            Task.created_at.desc()
        )
    ).all()

    return {
        "tasks": [

            {
                "task_id":
                    task.id,

                "status":
                    task.status,

                "goal":
                    task.goal,

                "revision_count":
                    task.revision_count,

                "current_task_id":
                    task.current_task_id,

                "completed_tasks":
                    get_completed_tasks(task),

                "created_at":
                    task.created_at
            }

            for task in tasks
        ]
    }


# ============================================================
# GET SINGLE TASK
# ============================================================

@app.get("/tasks/{task_id}")
def get_task(
    task_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    task = db.scalar(
        select(Task)
        .where(
            Task.id == task_id,
            Task.user_id ==
                current_user.id
        )
    )

    if task is None:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,
            detail=
                "Task not found."
        )

    if task.status == "STOPPED":

        return task_response(task)

    config = {
        "configurable": {
            "thread_id":
                str(task.id)
        }
    }

    try:

        state_snapshot = (
            workflow_app.get_state(
                config
            )
        )

    except Exception:

        state_snapshot = None

    if (
        state_snapshot is None
        or not state_snapshot.values
    ):

        return task_response(task)

    state = state_snapshot.values

    sync_task_from_state(
        task,
        state,
        db
    )

    return task_response(task)


# ============================================================
# GET TASK ARTIFACTS
# ============================================================

@app.get(
    "/tasks/{task_id}/artifacts"
)
def get_task_artifacts(
    task_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    task = db.scalar(
        select(Task)
        .where(
            Task.id == task_id,
            Task.user_id ==
                current_user.id
        )
    )

    if task is None:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,
            detail=
                "Task not found."
        )

    return {
        "task_id": task.id,

        "artifacts":
            list_artifacts(task.id)
    }


# ============================================================
# DOWNLOAD TASK ARTIFACT
# ============================================================

@app.get(
    "/tasks/{task_id}/artifacts/{filename}"
)
def download_task_artifact(
    task_id: int,
    filename: str,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    task = db.scalar(
        select(Task)
        .where(
            Task.id == task_id,
            Task.user_id ==
                current_user.id
        )
    )

    if task is None:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,
            detail=
                "Task not found."
        )

    try:

        artifact_path = get_artifact_path(
            task.id,
            filename
        )

    except (
        TypeError,
        ValueError,
        RuntimeError
    ) as exc:

        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,
            detail=
                "Invalid artifact filename."
        ) from exc

    if not artifact_path.is_file():

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,
            detail=
                "Artifact not found."
        )

    return FileResponse(
        path=artifact_path,
        filename=artifact_path.name,
        media_type="application/octet-stream"
    )


# ============================================================
# CREATE PUBLIC SHARE LINK
# ============================================================

@app.post(
    "/tasks/{task_id}/share"
)
def create_share_link(
    task_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    task = db.scalar(
        select(Task)
        .where(
            Task.id == task_id,
            Task.user_id ==
                current_user.id
        )
    )

    if task is None:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,
            detail=
                "Task not found."
        )

    if task.status != "COMPLETED":

        raise HTTPException(
            status_code=
                status.HTTP_409_CONFLICT,
            detail=(
                "Only completed tasks "
                "can be shared."
            )
        )

    existing_share = db.scalar(
        select(TaskShare)
        .where(
            TaskShare.task_id == task.id
        )
    )

    if existing_share is not None:

        return {
            "task_id": task.id,

            "share_token":
                existing_share.token,

            "share_url":
                f"/share/{existing_share.token}"
        }

    token = None

    for _ in range(5):

        candidate = secrets.token_urlsafe(
            32
        )

        existing_token = db.scalar(
            select(TaskShare)
            .where(
                TaskShare.token ==
                    candidate
            )
        )

        if existing_token is None:

            token = candidate

            break

    if token is None:

        raise HTTPException(
            status_code=
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=
                "Could not generate a share link."
        )

    share = TaskShare(
        task_id=task.id,
        token=token
    )

    db.add(share)

    db.commit()

    db.refresh(share)

    return {
        "task_id": task.id,

        "share_token":
            share.token,

        "share_url":
            f"/share/{share.token}"
    }


# ============================================================
# GET PUBLIC SHARED TASK
# ============================================================

@app.get(
    "/share/{token}"
)
def get_shared_task(
    token: str,
    db: Session = Depends(get_db)
):

    share = db.scalar(
        select(TaskShare)
        .where(
            TaskShare.token == token
        )
    )

    if share is None:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,
            detail=
                "Shared task not found."
        )

    task = db.scalar(
        select(Task)
        .where(
            Task.id == share.task_id
        )
    )

    if task is None:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,
            detail=
                "Shared task not found."
        )

    return task_response(task)


# ============================================================
# STOP TASK
# ============================================================

@app.post("/tasks/{task_id}/stop")
def stop_task(
    task_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    task = db.scalar(
        select(Task)
        .where(
            Task.id == task_id,
            Task.user_id ==
                current_user.id
        )
    )

    if task is None:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,
            detail=
                "Task not found."
        )

    terminal_statuses = {
        "COMPLETED",
        "FAILED",
        "STOPPED"
    }

    if task.status in terminal_statuses:

        raise HTTPException(
            status_code=
                status.HTTP_409_CONFLICT,
            detail=(
                f"Task cannot be stopped because "
                f"it is already {task.status}."
            )
        )

    task.status = "STOPPED"

    task.current_task_id = None

    db.commit()

    db.refresh(task)

    return task_response(task)


# ============================================================
# DELETE TASK
# ============================================================

@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    task = db.scalar(
        select(Task)
        .where(
            Task.id == task_id,
            Task.user_id ==
                current_user.id
        )
    )

    if task is None:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,
            detail=
                "Task not found."
        )

    deletable_statuses = {
        "COMPLETED",
        "FAILED",
        "STOPPED"
    }

    if task.status not in deletable_statuses:

        raise HTTPException(
            status_code=
                status.HTTP_409_CONFLICT,
            detail=(
                "Only completed, failed, or stopped "
                "tasks can be deleted. Stop a running "
                "task before deleting it."
            )
        )

    delete_task_artifacts(
        task.id
    )

    db.delete(task)

    db.commit()

    return {
        "message":
            "Task deleted successfully.",

        "task_id":
            task_id
    }


# ============================================================
# HUMAN APPROVAL
# ============================================================

@app.post(
    "/tasks/{task_id}/approval"
)
def submit_approval(
    task_id: int,
    request: ApprovalRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    task = db.scalar(
        select(Task)
        .where(
            Task.id == task_id,
            Task.user_id ==
                current_user.id
        )
    )

    if task is None:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,
            detail=
                "Task not found."
        )

    if (
        request.approved is False
        and not request.feedback.strip()
    ):

        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,
            detail=(
                "Feedback is required when "
                "rejecting an implementation."
            )
        )

    if task.status != "WAITING_FOR_HUMAN":

        raise HTTPException(
            status_code=
                status.HTTP_409_CONFLICT,
            detail=(
                "This task is not currently "
                "waiting for human approval."
            )
        )

    config = {
        "configurable": {
            "thread_id":
                str(task.id)
        }
    }

    resume_value = {
        "approved":
            request.approved
    }

    if not request.approved:

        resume_value["feedback"] = (
            request.feedback.strip()
        )

    try:

        result = workflow_app.invoke(
            Command(
                resume=resume_value
            ),
            config
        )

    except Exception as exc:

        raise HTTPException(
            status_code=
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=
                "Task could not be resumed."
        ) from exc

    sync_task_from_state(
        task,
        result,
        db
    )

    return task_response(task)

