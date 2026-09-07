from graph.state import AgentState


def test_initial_state():

    state: AgentState = {
        "user_goal": "Build a FastAPI application",
        "plan": "",
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

    assert state["user_goal"] == "Build a FastAPI application"
    assert state["revision_count"] == 0
    assert state["revision_reason"] == "INITIAL"
    assert state["status"] == "STARTING"