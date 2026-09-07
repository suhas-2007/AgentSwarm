import graph.nodes as nodes


def test_revision_count_increases(monkeypatch):

    def fake_coder_agent(
        goal,
        task_description,
        research,
        evaluation,
        human_feedback
    ):
        return "FAKE GENERATED CODE"

    monkeypatch.setattr(
        nodes,
        "coder_agent",
        fake_coder_agent
    )

    state = {
        "user_goal": "Build a FastAPI application",

        "plan": "Create API endpoints",

        "plan_tasks": [
            {
                "task_id": 1,
                "description": "Research FastAPI requirements",
                "agent": "researcher",
                "task_type": "research",
                "depends_on": []
            },
            {
                "task_id": 2,
                "description": "Implement the FastAPI application",
                "agent": "coder",
                "task_type": "coding",
                "depends_on": [1]
            }
        ],

        "current_task_id": 2,

        "completed_tasks": [1, 2],

        "research": "FastAPI uses Pydantic for validation",

        "code": "",

        "content": "",

        "evaluation": "VERDICT: REVISE",

        "final_answer": "",

        "revision_count": 0,

        "human_approval": "",

        "human_feedback": "",

        "revision_reason": "EVALUATOR_REVISE",

        "status": "REVISING"
    }

    result = nodes.revision_node(state)

    assert result["current_task_id"] == 2

    assert result["revision_count"] == 1

    assert result["code"] == "FAKE GENERATED CODE"

    assert result["revision_reason"] == "INITIAL"

    assert result["human_feedback"] == ""

    assert result["status"] == "REVISING"