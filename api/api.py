import json
import os
import secrets
from contextlib import asynccontextmanager

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from langgraph.types import Command

from pydantic import BaseModel

from sqlalchemy import (
    delete,
    inspect,
    select,
    text,
    update
)

from sqlalchemy.orm import Session

from database.connection import Base, SessionLocal, engine, get_db
from database.models import Task, TaskShare, User

from auth.dependencies import get_current_user
from auth.routes import router as auth_router

from graph.workflow import app as workflow_app

from artifacts.manager import (
    delete_task_artifacts,
    get_artifact_path,
    list_artifacts
)

from services.task_control import (
    validate_status_transition
)

from services.task_runner import run_task


def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)
        if "users" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("users")]
            with engine.connect() as conn:
                if "google_id" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR(255)"))
                if "auth_provider" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN auth_provider VARCHAR(50) DEFAULT 'local'"))
                if "name" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR(255)"))
                if "avatar_url" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)"))
                if "gemini_api_key" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN gemini_api_key TEXT"))
                if "groq_api_key" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN groq_api_key TEXT"))
                if "tavily_api_key" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN tavily_api_key TEXT"))
                conn.commit()
    except Exception as exc:
        print(f"[DB INIT] Table check notice: {exc}", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AgentSwarm API",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class CreateTaskRequest(BaseModel):
    goal: str


class ApprovalRequest(BaseModel):
    approved: bool
    feedback: str = ""


# ============================================================
# CORS CONFIGURATION
# ============================================================

def get_allowed_origins() -> list[str]:
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        cleaned_frontend = frontend_url.strip().rstrip("/")
        if cleaned_frontend and cleaned_frontend not in origins:
            origins.append(cleaned_frontend)

    additional_origins = os.getenv("ALLOWED_ORIGINS")
    if additional_origins:
        for origin in additional_origins.split(","):
            cleaned = origin.strip().rstrip("/")
            if cleaned and cleaned not in origins:
                origins.append(cleaned)

    return origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_origin_regex=r"https:\/\/.*\.onrender\.com|https:\/\/.*\.up\.railway\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


router = APIRouter()


# ============================================================
# BACKGROUND TASK
# ============================================================

def run_task_background(
    task_id: int
):
    """
    Execute an AgentSwarm task in the background.
    """

    try:

        run_task(task_id)

    except Exception as error:

        print(
            f"[API] Background task {task_id} "
            f"failed: {error}",
            flush=True
        )


# ============================================================
# DATABASE STATE SYNCHRONIZATION
# ============================================================

def sync_task_from_state(
    task: Task,
    state: dict,
    db
):
    """
    Synchronize the database with the latest
    LangGraph checkpoint.

    A STOPPED task cannot be overwritten.
    """

    new_status = state.get(
        "status",
        task.status
    )

    values = {
        "status": new_status,

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

        values["completed_tasks"] = json.dumps(
            completed_tasks
        )

    # Do not overwrite a task that the user
    # has already stopped.

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

    return result.rowcount == 1


# ============================================================
# COMPLETED TASKS
# ============================================================

def get_completed_tasks(
    task: Task
) -> list[int]:

    if not task.completed_tasks:

        return []

    try:

        value = json.loads(
            task.completed_tasks
        )

        if isinstance(value, list):

            return [
                int(item)
                for item in value
            ]

    except (
        ValueError,
        TypeError,
        json.JSONDecodeError
    ):

        pass

    return []


# ============================================================
# TASK RESPONSE
# ============================================================

def task_response(
    task: Task
) -> dict:

    return {
        "id": task.id,
        "task_id": task.id,
        "goal": task.goal,
        "status": task.status,
        "plan": task.plan,
        "research": task.research,
        "content": task.content,
        "code": task.code,
        "evaluation": task.evaluation,
        "final_answer": task.final_answer,
        "revision_count": task.revision_count,
        "current_task_id": task.current_task_id,
        "completed_tasks": get_completed_tasks(
            task
        ),
        "created_at": task.created_at
    }


# ============================================================
# HEALTH
# ============================================================

@router.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "AgentSwarm"
    }


# ============================================================
# CREATE TASK
# ============================================================

@router.post("/tasks")
def create_task(
    request: CreateTaskRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    goal = request.goal.strip()

    if not goal:

        raise HTTPException(
            status_code=422,
            detail="Goal cannot be empty."
        )

    task = Task(
        user_id=current_user.id,
        goal=goal,
        status="STARTING"
    )

    db.add(task)

    db.commit()

    db.refresh(task)

    task_id = task.id

    response = task_response(
        task
    )

    background_tasks.add_task(
        run_task_background,
        task_id
    )

    return response


# ============================================================
# LIST TASKS
# ============================================================

@router.get("/tasks")
def list_tasks(
    current_user=Depends(
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

    return [
        task_response(task)
        for task in tasks
    ]


# ============================================================
# GET TASK
# ============================================================

@router.get("/tasks/{task_id}")
def get_task(
    task_id: int,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    task = db.scalar(
        select(Task).where(
            Task.id == task_id,
            Task.user_id ==
            current_user.id
        )
    )

    if task is None:

        raise HTTPException(
            status_code=404,
            detail="Task not found."
        )

    if task.status != "STOPPED":

        config = {
            "configurable": {
                "thread_id":
                    str(task.id)
            }
        }

        try:

            snapshot = (
                workflow_app.get_state(
                    config
                )
            )

            if (
                snapshot is not None
                and snapshot.values
            ):

                sync_task_from_state(
                    task,
                    snapshot.values,
                    db
                )

        except Exception as error:

            print(
                f"[API] Could not synchronize "
                f"task {task.id}: {error}",
                flush=True
            )

    return task_response(
        task
    )


# ============================================================
# LIST ARTIFACTS
# ============================================================

@router.get(
    "/tasks/{task_id}/artifacts"
)
def get_artifacts(
    task_id: int,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    task = db.scalar(
        select(Task).where(
            Task.id == task_id,
            Task.user_id ==
            current_user.id
        )
    )

    if task is None:

        raise HTTPException(
            status_code=404,
            detail="Task not found."
        )

    return list_artifacts(
        task_id
    )


# ============================================================
# DOWNLOAD ARTIFACT
# ============================================================

@router.get(
    "/tasks/{task_id}/artifacts/{filename}"
)
def download_artifact(
    task_id: int,
    filename: str,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    task = db.scalar(
        select(Task).where(
            Task.id == task_id,
            Task.user_id ==
            current_user.id
        )
    )

    if task is None:

        raise HTTPException(
            status_code=404,
            detail="Task not found."
        )

    try:

        artifact_path = get_artifact_path(
            task_id,
            filename
        )

    except (
        ValueError,
        TypeError,
        RuntimeError
    ) as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    if not artifact_path.is_file():

        raise HTTPException(
            status_code=404,
            detail="Artifact not found."
        )

    return FileResponse(
        path=artifact_path,
        filename=artifact_path.name
    )


# ============================================================
# CREATE SHARE
# ============================================================

@router.post(
    "/tasks/{task_id}/share"
)
def create_share(
    task_id: int,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    task = db.scalar(
        select(Task).where(
            Task.id == task_id,
            Task.user_id ==
            current_user.id
        )
    )

    if task is None:

        raise HTTPException(
            status_code=404,
            detail="Task not found."
        )

    if task.status != "COMPLETED":

        raise HTTPException(
            status_code=400,
            detail=(
                "Only completed tasks "
                "can be shared."
            )
        )

    token = secrets.token_urlsafe(
        32
    )

    share = TaskShare(
        task_id=task.id,
        token=token
    )

    db.add(share)

    db.commit()

    return {
        "token": token
    }


# ============================================================
# PUBLIC SHARE
# ============================================================

@router.get(
    "/share/{token}"
)
def get_shared_task(
    token: str,
    db: Session = Depends(get_db)
):

    share = db.scalar(
        select(TaskShare).where(
            TaskShare.token == token
        )
    )

    if share is None:

        raise HTTPException(
            status_code=404,
            detail="Share not found."
        )

    task = db.scalar(
        select(Task).where(
            Task.id == share.task_id
        )
    )

    if task is None:

        raise HTTPException(
            status_code=404,
            detail="Task not found."
        )

    if task.status != "COMPLETED":

        raise HTTPException(
            status_code=403,
            detail="Shared task is not completed."
        )

    return {
        "task_id": task.id,
        "status": task.status,
        "goal": task.goal,
        "evaluation": task.evaluation,
        "final_answer":
            task.final_answer,
        "revision_count":
            task.revision_count
    }


# ============================================================
# STOP TASK
# ============================================================

@router.post(
    "/tasks/{task_id}/stop"
)
def stop_task(
    task_id: int,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    task = db.scalar(
        select(Task).where(
            Task.id == task_id,
            Task.user_id ==
            current_user.id
        )
    )

    if task is None:

        raise HTTPException(
            status_code=404,
            detail="Task not found."
        )

    if task.status in (
        "COMPLETED",
        "FAILED",
        "STOPPED"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                f"Task is already "
                f"{task.status}."
            )
        )

    current_status = task.status

    validate_status_transition(
        current_status,
        "STOPPED"
    )

    result = db.execute(
        update(Task)
        .where(
            Task.id == task.id,
            Task.user_id ==
            current_user.id,
            Task.status ==
            current_status,
            Task.status != "STOPPED"
        )
        .values(
            status="STOPPED",
            current_task_id=None
        )
    )

    db.commit()

    if result.rowcount != 1:

        db.refresh(task)

        raise HTTPException(
            status_code=409,
            detail=(
                "Task changed while "
                "stopping it. Please "
                "refresh and try again."
            )
        )

    db.refresh(task)

    return task_response(
        task
    )


# ============================================================
# DELETE TASK
# ============================================================

@router.delete(
    "/tasks/{task_id}"
)
def delete_task(
    task_id: int,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    task = db.scalar(
        select(Task).where(
            Task.id == task_id,
            Task.user_id ==
            current_user.id
        )
    )

    if task is None:

        raise HTTPException(
            status_code=404,
            detail="Task not found."
        )

    if task.status not in (
        "COMPLETED",
        "FAILED",
        "STOPPED"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only completed, failed, "
                "or stopped tasks can "
                "be deleted."
            )
        )

    delete_task_artifacts(
        task.id
    )

    db.execute(
        delete(Task).where(
            Task.id == task.id,
            Task.user_id == current_user.id
        )
    )

    db.commit()

    return {
        "message": "Task deleted."
    }


# ============================================================
# HUMAN APPROVAL / REJECTION
# ============================================================

@router.post(
    "/tasks/{task_id}/approval"
)
def approve_task(
    task_id: int,
    request: ApprovalRequest,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    approved = request.approved
    feedback = request.feedback.strip()

    task = db.scalar(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == current_user.id
        )
    )

    if task is None:

        raise HTTPException(
            status_code=404,
            detail="Task not found."
        )

    if task.status != "WAITING_FOR_HUMAN":

        raise HTTPException(
            status_code=400,
            detail=(
                "Task is not waiting "
                "for human review."
            )
        )

    if (
        not approved
        and not feedback
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Feedback is required when "
                "rejecting an implementation."
            )
        )

    config = {
        "configurable": {
            "thread_id":
                str(task.id)
        }
    }

    resume_value = {
        "approved": approved
    }

    if not approved:

        resume_value["feedback"] = feedback

    try:

        result_state = (
            workflow_app.invoke(
                Command(
                    resume=resume_value
                ),
                config
            )
        )

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Could not resume task."
        ) from error

    sync_task_from_state(
        task,
        result_state,
        db
    )

    return task_response(
        task
    )


# ============================================================
# REGISTER AUTH ROUTES
# ============================================================

app.include_router(
    auth_router
)


# ============================================================
# REGISTER API ROUTES
# ============================================================

app.include_router(
    router
)