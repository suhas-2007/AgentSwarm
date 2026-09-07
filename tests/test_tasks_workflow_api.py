from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import api.api as api_module

from database.connection import Base, get_db
from database.models import User
from auth.dependencies import get_current_user


engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base.metadata.create_all(bind=engine)


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


def test_tasks_endpoint_runs_workflow(monkeypatch):

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