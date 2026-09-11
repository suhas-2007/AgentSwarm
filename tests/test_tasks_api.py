from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import api.api as api_module

from database.connection import Base, get_db
from database.models import User
from auth.dependencies import get_current_user


from tests.conftest import TestingSessionLocal


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    db = TestingSessionLocal()

    user = db.query(User).filter(
        User.email == "test@example.com"
    ).first()

    if user is None:
        user = User(
            email="test@example.com",
            password_hash="test-password"
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    db.close()

    return user


api_module.app.dependency_overrides[
    get_db
] = override_get_db

api_module.app.dependency_overrides[
    get_current_user
] = override_get_current_user


client = TestClient(api_module.app)


def test_create_task(monkeypatch):

    captured = {}

    def fake_run_task(
        task_id
    ):

        captured["task_id"] = task_id

    monkeypatch.setattr(
        api_module,
        "run_task",
        fake_run_task
    )

    response = client.post(
        "/tasks",
        json={
            "goal": "Build a FastAPI application"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(
        data["task_id"],
        int
    )

    assert data["status"] == "STARTING"

    assert data["goal"] == (
        "Build a FastAPI application"
    )

    assert data["plan"] == ""

    assert data["research"] == ""

    assert data["code"] == ""

    assert data["evaluation"] == ""

    assert data["final_answer"] == ""

    assert data["revision_count"] == 0

    assert captured["task_id"] == (
        data["task_id"]
    )


def test_create_task_rejects_empty_goal():

    response = client.post(
        "/tasks",
        json={
            "goal": ""
        }
    )

    assert response.status_code == 422


def test_create_task_rejects_missing_goal():

    response = client.post(
        "/tasks",
        json={}
    )

    assert response.status_code == 422


def test_approval_requires_feedback_when_rejected(db_session):

    db = db_session

    user = db.query(User).filter(
        User.email == "test@example.com"
    ).first()

    if user is None:
        user = User(
            email="test@example.com",
            password_hash="test-password"
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    from database.models import Task

    task = Task(
        user_id=user.id,
        goal="Test task",
        status="WAITING_FOR_HUMAN"
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    task_id = task.id

    response = client.post(
        f"/tasks/{task_id}/approval",
        json={
            "approved": False,
            "feedback": ""
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Feedback is required when rejecting "
        "an implementation."
    )


def test_list_tasks_returns_list(db_session):
    db = db_session
    user = db.query(User).filter(
        User.email == "test@example.com"
    ).first()
    if user is None:
        user = User(
            email="test@example.com",
            password_hash="test-password"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    from database.models import Task
    task = Task(
        user_id=user.id,
        goal="Task for list test",
        status="COMPLETED"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(item["task_id"] == task.id for item in data)


def test_list_artifacts_returns_list(db_session):
    db = db_session
    user = db.query(User).filter(
        User.email == "test@example.com"
    ).first()
    if user is None:
        user = User(
            email="test@example.com",
            password_hash="test-password"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    from database.models import Task
    task = Task(
        user_id=user.id,
        goal="Artifact test task",
        status="COMPLETED"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.get(f"/tasks/{task.id}/artifacts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_task_created_at_utc_serialization(db_session):
    db = db_session
    user = db.query(User).filter(
        User.email == "test@example.com"
    ).first()
    if user is None:
        user = User(
            email="test@example.com",
            password_hash="test-password"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    from database.models import Task
    task = Task(
        user_id=user.id,
        goal="Timezone test task",
        status="COMPLETED"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    matching = next((item for item in data if item["task_id"] == task.id), None)
    assert matching is not None
    assert "created_at" in matching
    assert matching["created_at"] is not None
    # Must have UTC timezone indicator (+00:00 or Z)
    assert matching["created_at"].endswith("Z") or "+00:00" in matching["created_at"]