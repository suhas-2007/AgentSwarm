from graph.workflow import (
    evaluator_route,
    human_route,
    task_router,
    MAX_REVISIONS,
)


def base_state():
    return {
        "task_id": 1,
        "user_goal": "Build a test application",
        "plan": "",
        "plan_tasks": [
            {
                "task_id": 1,
                "description": "Research the requirements",
                "agent": "researcher",
                "task_type": "research",
                "depends_on": [],
            },
            {
                "task_id": 2,
                "description": "Implement the application",
                "agent": "coder",
                "task_type": "coding",
                "depends_on": [1],
            },
        ],
        "current_task_id": 1,
        "completed_tasks": [],
        "research": "",
        "code": "",
        "content": "",
        "evaluation": "",
        "final_answer": "",
        "revision_count": 0,
        "human_approval": "",
        "human_feedback": "",
        "revision_reason": "",
        "status": "",
    }


def test_task_router_researcher():
    state = base_state()

    result = task_router(state)

    assert result == "researcher"

    print("PASS: researcher routing")


def test_task_router_coder():
    state = base_state()

    state["current_task_id"] = 2

    result = task_router(state)

    assert result == "coder"

    print("PASS: coder routing")


def test_task_router_evaluator():
    state = base_state()

    state["current_task_id"] = None

    result = task_router(state)

    assert result == "evaluator"

    print("PASS: evaluator routing")


def test_evaluator_pass_routes_to_human():
    state = base_state()

    state["evaluation"] = """
    VERDICT: PASS
    The implementation satisfies the requirements.
    """

    result = evaluator_route(state)

    assert result == "human"

    print("PASS: evaluator PASS -> human")


def test_evaluator_revise_routes_to_revision():
    state = base_state()

    state["evaluation"] = """
    VERDICT: REVISE
    The implementation has an important issue.
    """

    state["revision_count"] = 0

    result = evaluator_route(state)

    assert result == "revision"

    print("PASS: evaluator REVISE -> revision")


def test_evaluator_revision_limit_routes_to_human():
    state = base_state()

    state["evaluation"] = """
    VERDICT: REVISE
    The implementation still has an issue.
    """

    state["revision_count"] = MAX_REVISIONS

    result = evaluator_route(state)

    assert result == "human"

    print("PASS: evaluator revision limit")


def test_evaluator_unavailable():
    state = base_state()

    state["evaluation"] = """
    EVALUATION_UNAVAILABLE

    REASON: Gemini evaluator quota has been exhausted.
    """

    result = evaluator_route(state)

    assert result == "evaluation_unavailable"

    print("PASS: evaluator unavailable routing")


def test_human_approve_routes_to_finalizer():
    state = base_state()

    state["human_approval"] = "APPROVE"

    result = human_route(state)

    assert result == "finalizer"

    print("PASS: human APPROVE -> finalizer")


def test_human_reject_routes_to_revision():
    state = base_state()

    state["human_approval"] = "REJECT"
    state["revision_count"] = 0

    result = human_route(state)

    assert result == "revision"

    print("PASS: human REJECT -> revision")


def test_human_reject_at_revision_limit():
    state = base_state()

    state["human_approval"] = "REJECT"
    state["revision_count"] = MAX_REVISIONS

    result = human_route(state)

    assert result == "end"

    print("PASS: human rejection revision limit")


def run_tests():
    print("=" * 60)
    print("AgentSwarm Workflow Routing Tests")
    print("=" * 60)

    test_task_router_researcher()
    test_task_router_coder()
    test_task_router_evaluator()

    test_evaluator_pass_routes_to_human()
    test_evaluator_revise_routes_to_revision()
    test_evaluator_revision_limit_routes_to_human()
    test_evaluator_unavailable()

    test_human_approve_routes_to_finalizer()
    test_human_reject_routes_to_revision()
    test_human_reject_at_revision_limit()

    print()
    print("=" * 60)
    print("ALL WORKFLOW ROUTING TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()