import pytest
from fastapi.testclient import TestClient

from auth.security import create_access_token, hash_password
from database.models import Task, TaskShare, User
import api.api as api_module


@pytest.fixture
def user_a(db_session):
    user = User(
        email="usera@example.com",
        password_hash=hash_password("Password123!")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_b(db_session):
    user = User(
        email="userb@example.com",
        password_hash=hash_password("Password123!")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def client_user_b(user_b):
    token = create_access_token(user_b.id)
    with TestClient(api_module.app) as test_client:
        test_client.headers["Authorization"] = f"Bearer {token}"
        yield test_client


def test_cross_user_task_isolation(client_user_b, db_session, user_a):
    """Ensure User B cannot view, modify, stop, delete, share or approve User A's task."""
    task_a = Task(
        goal="Private goal of User A",
        status="WAITING_FOR_HUMAN",
        user_id=user_a.id
    )
    db_session.add(task_a)
    db_session.commit()
    db_session.refresh(task_a)

    # User B attempts to read User A's task
    res_get = client_user_b.get(f"/tasks/{task_a.id}")
    assert res_get.status_code == 404

    # User B attempts to list artifacts
    res_art = client_user_b.get(f"/tasks/{task_a.id}/artifacts")
    assert res_art.status_code == 404

    # User B attempts to stop User A's task
    res_stop = client_user_b.post(f"/tasks/{task_a.id}/stop")
    assert res_stop.status_code == 404

    # User B attempts to delete User A's task
    res_del = client_user_b.delete(f"/tasks/{task_a.id}")
    assert res_del.status_code == 404

    # User B attempts to share User A's task
    res_share = client_user_b.post(f"/tasks/{task_a.id}/share")
    assert res_share.status_code == 404

    # User B attempts to approve User A's task
    res_approve = client_user_b.post(
        f"/tasks/{task_a.id}/approval",
        json={"approved": True, "feedback": ""}
    )
    assert res_approve.status_code == 404


def test_share_token_security_and_sanitization(client, db_session, test_user):
    """Ensure share tokens only expose intended completed task data and block incomplete tasks."""
    completed_task = Task(
        goal="Completed research",
        status="COMPLETED",
        evaluation="VERDICT: PASS",
        final_answer="High quality report",
        revision_count=1,
        user_id=test_user.id
    )
    running_task = Task(
        goal="Confidential in-progress code",
        status="RUNNING",
        user_id=test_user.id
    )
    db_session.add_all([completed_task, running_task])
    db_session.commit()

    share_comp = TaskShare(task_id=completed_task.id, token="valid-completed-token")
    share_run = TaskShare(task_id=running_task.id, token="running-task-token")
    db_session.add_all([share_comp, share_run])
    db_session.commit()

    # Completed task share returns 200 with sanitized fields
    res_comp = client.get("/share/valid-completed-token")
    assert res_comp.status_code == 200
    data = res_comp.json()
    assert data["task_id"] == completed_task.id
    assert data["status"] == "COMPLETED"
    assert data["goal"] == "Completed research"
    assert data["final_answer"] == "High quality report"
    assert "user_id" not in data
    assert "email" not in data

    # Non-completed task share returns 403 Forbidden
    res_run = client.get("/share/running-task-token")
    assert res_run.status_code == 403
    assert "not completed" in res_run.json()["detail"].lower()

    # Non-existent token returns 404
    res_none = client.get("/share/non-existent-token")
    assert res_none.status_code == 404


def test_auth_route_mounting_and_password_validation(client):
    """Verify that auth endpoints are properly reachable at /auth/* and enforce password policy."""
    # Weak password (<8 characters)
    weak_signup = client.post(
        "/auth/signup",
        json={"email": "newuser@example.com", "password": "short"}
    )
    assert weak_signup.status_code == 422

    # Successful signup
    good_signup = client.post(
        "/auth/signup",
        json={"email": "newuser@example.com", "password": "Password123!"}
    )
    assert good_signup.status_code == 201
    assert "access_token" in good_signup.json()

    # Login works
    login_res = client.post(
        "/auth/login",
        json={"email": "newuser@example.com", "password": "Password123!"}
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()
