from graph.workflow import evaluator_route, human_route


def test_evaluator_routes_to_revision():

    state = {
        "user_goal": "Build a FastAPI application",
        "plan": "",
        "research": "",
        "code": "",
        "evaluation": "VERDICT: REVISE",
        "final_answer": "",

        "revision_count": 0,

        "human_approval": "",
        "human_feedback": "",

        "revision_reason": "INITIAL",

        "status": "EVALUATING"
    }

    result = evaluator_route(state)

    assert result == "revision"


def test_evaluator_routes_to_human_on_pass():

    state = {
        "user_goal": "Build a FastAPI application",
        "plan": "",
        "research": "",
        "code": "",
        "evaluation": "VERDICT: PASS",
        "final_answer": "",

        "revision_count": 0,

        "human_approval": "",
        "human_feedback": "",

        "revision_reason": "INITIAL",

        "status": "EVALUATING"
    }

    result = evaluator_route(state)

    assert result == "human"


def test_approved_human_routes_to_finalizer():

    state = {
        "user_goal": "Build a FastAPI application",
        "plan": "",
        "research": "",
        "code": "",
        "evaluation": "VERDICT: PASS",
        "final_answer": "",

        "revision_count": 0,

        "human_approval": "APPROVE",
        "human_feedback": "",

        "revision_reason": "INITIAL",

        "status": "WAITING_FOR_HUMAN"
    }

    result = human_route(state)

    assert result == "finalizer"


def test_rejected_human_routes_to_revision():

    state = {
        "user_goal": "Build a FastAPI application",
        "plan": "",
        "research": "",
        "code": "",
        "evaluation": "VERDICT: PASS",
        "final_answer": "",

        "revision_count": 0,

        "human_approval": "REJECT",
        "human_feedback": "Add better error handling.",

        "revision_reason": "INITIAL",

        "status": "WAITING_FOR_HUMAN"
    }

    result = human_route(state)

    assert result == "revision"