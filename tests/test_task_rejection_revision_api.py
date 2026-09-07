from database.models import Task

import api.api as api_module


def create_test_task(test_user, db_session):

    task = Task(
        user_id=test_user.id,
        goal="Build a calculator",
        status="WAITING_FOR_HUMAN"
    )

    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    return task.id


def test_reject_task_triggers_revision(
    client,
    test_user,
    db_session,
    monkeypatch
):

    task_id = create_test_task(
        test_user,
        db_session
    )

    captured = {}

    def fake_workflow_invoke(
        command,
        config
    ):

        captured["command"] = command
        captured["config"] = config

        return {
            "user_goal": "Build a calculator",
            "plan": "Create calculator functions.",
            "research": (
                "Research calculator implementation."
            ),
            "code": (
                "Revised calculator implementation."
            ),
            "evaluation": "VERDICT: REVISE",
            "final_answer": "",
            "revision_count": 1,
            "human_approval": "REJECT",
            "human_feedback": (
                "Improve error handling."
            ),
            "revision_reason": "HUMAN_REJECT",
            "status": "REVISING"
        }

    monkeypatch.setattr(
        api_module.workflow_app,
        "invoke",
        fake_workflow_invoke
    )

    response = client.post(
        f"/tasks/{task_id}/approval",
        json={
            "approved": False,
            "feedback": (
                "  Improve error handling.  "
            )
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["task_id"] == task_id
    assert data["status"] == "REVISING"
    assert data["revision_count"] == 1

    assert captured["config"] == {
        "configurable": {
            "thread_id": str(task_id)
        }
    }

    assert captured["command"].resume == {
        "approved": False,
        "feedback": "Improve error handling."
    }