from graph.workflow import evaluator_route, human_route


def test_evaluator_stops_revision_at_maximum():

    state = {
        "user_goal": "Build a FastAPI application",
        "plan": "",
        "research": "",
        "code": "",
        "evaluation": "VERDICT: REVISE",
        "final_answer": "",

        "revision_count": 2,

        "human_approval": "",
        "human_feedback": "",

        "revision_reason": "INITIAL",

        "status": "EVALUATING"
    }

    result = evaluator_route(state)

    assert result == "human"


def test_human_rejection_stops_at_maximum():

    state = {
        "user_goal": "Build a FastAPI application",
        "plan": "",
        "research": "",
        "code": "",
        "evaluation": "VERDICT: REVISE",
        "final_answer": "",

        "revision_count": 2,

        "human_approval": "REJECT",
        "human_feedback": "The implementation still needs changes.",

        "revision_reason": "INITIAL",

        "status": "WAITING_FOR_HUMAN"
    }

    result = human_route(state)

    assert result == "end"