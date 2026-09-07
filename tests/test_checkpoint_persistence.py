from uuid import uuid4

from graph.workflow import app


def test_checkpoint_persists_state():

    thread_id = (
        f"checkpoint-test-{uuid4()}"
    )

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    initial_state = {
        "user_goal": "Test checkpoint persistence",

        "plan": "",
        "plan_tasks": [],

        "current_task_id": None,
        "completed_tasks": [],

        "research": "",
        "code": "",
        "evaluation": "",
        "final_answer": "",

        "revision_count": 0,

        "human_approval": "",
        "human_feedback": "",

        "revision_reason": "INITIAL",

        "status": "STARTING"
    }

    app.update_state(
        config,
        initial_state
    )

    restored_state = app.get_state(
        config
    )

    assert restored_state.values[
        "user_goal"
    ] == "Test checkpoint persistence"

    assert restored_state.values[
        "revision_count"
    ] == 0

    assert restored_state.values[
        "status"
    ] == "STARTING"

    assert restored_state.values[
        "plan_tasks"
    ] == []

    assert restored_state.values[
        "completed_tasks"
    ] == []

    assert restored_state.values[
        "current_task_id"
    ] is None