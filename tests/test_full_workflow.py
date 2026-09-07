import importlib

import graph.human as human
import graph.nodes as nodes
import graph.workflow as workflow_module


def test_complete_workflow_with_approval(monkeypatch):

    # --------------------------------------------------
    # Fake Planner
    # --------------------------------------------------

    def fake_planner_agent(goal):

        return {
            "tasks": [
                {
                    "task_id": 1,
                    "description": (
                        "Create the application structure."
                    ),
                    "agent": "researcher",
                    "task_type": "research",
                    "depends_on": []
                },
                {
                    "task_id": 2,
                    "description": (
                        "Implement the API endpoints."
                    ),
                    "agent": "coder",
                    "task_type": "coding",
                    "depends_on": [1]
                }
            ]
        }

    # --------------------------------------------------
    # Fake Researcher
    # --------------------------------------------------

    def fake_researcher_agent(
        goal,
        task_description
    ):

        return (
            "FastAPI supports Pydantic-based request "
            "validation."
        )

    # --------------------------------------------------
    # Fake Coder
    # --------------------------------------------------

    def fake_coder_agent(
        goal,
        task_description,
        research,
        evaluation,
        human_feedback
    ):

        return (
            "FastAPI application implementation."
        )

    # --------------------------------------------------
    # Fake Evaluator
    # --------------------------------------------------

    def fake_evaluator_agent(
        goal,
        task_description,
        research,
        code,
        content
    ):

        return (
            "VERDICT: PASS\n"
            "ISSUES: None"
        )

    # --------------------------------------------------
    # Fake Human Approval
    # --------------------------------------------------

    def fake_human_approval_node(state):

        return {
            **state,
            "human_approval": "APPROVE",
            "human_feedback": "",
            "status": "FINALIZING"
        }

    # --------------------------------------------------
    # Fake Finalizer
    # --------------------------------------------------

    def fake_finalizer_agent(
        goal,
        research,
        content,
        code,
        evaluation
    ):

        return (
            "Implementation completed successfully."
        )

    # --------------------------------------------------
    # Patch dependencies
    # --------------------------------------------------

    monkeypatch.setattr(
        nodes,
        "planner_agent",
        fake_planner_agent
    )

    monkeypatch.setattr(
        nodes,
        "researcher_agent",
        fake_researcher_agent
    )

    monkeypatch.setattr(
        nodes,
        "coder_agent",
        fake_coder_agent
    )

    monkeypatch.setattr(
        nodes,
        "evaluator_agent",
        fake_evaluator_agent
    )

    monkeypatch.setattr(
        human,
        "human_approval_node",
        fake_human_approval_node
    )

    monkeypatch.setattr(
        nodes,
        "finalizer_agent",
        fake_finalizer_agent
    )

    # --------------------------------------------------
    # Reload workflow after patching dependencies
    # --------------------------------------------------

    workflow = importlib.reload(
        workflow_module
    )

    # --------------------------------------------------
    # Initial AgentState
    # --------------------------------------------------

    initial_state = {
        "task_id": 1,

        "user_goal": "Build a FastAPI application",

        "plan": "",
        "plan_tasks": [],

        "current_task_id": None,
        "completed_tasks": [],

        "research": "",
        "code": "",
        "content": "",
        "evaluation": "",
        "final_answer": "",

        "revision_count": 0,

        "human_approval": "",
        "human_feedback": "",

        "revision_reason": "INITIAL",

        "status": "STARTING"
    }

    # --------------------------------------------------
    # Execute workflow with checkpoint thread
    # --------------------------------------------------

    config = {
        "configurable": {
            "thread_id": "test-full-workflow"
        }
    }

    result = workflow.app.invoke(
        initial_state,
        config
    )

    # --------------------------------------------------
    # Verify final result
    # --------------------------------------------------

    assert result["status"] == "COMPLETED"

    assert result["user_goal"] == (
        "Build a FastAPI application"
    )

    assert result["plan"] != ""

    assert result["plan_tasks"] == [
        {
            "task_id": 1,
            "description": (
                "Create the application structure."
            ),
            "agent": "researcher",
            "task_type": "research",
            "depends_on": []
        },
        {
            "task_id": 2,
            "description": (
                "Implement the API endpoints."
            ),
            "agent": "coder",
            "task_type": "coding",
            "depends_on": [1]
        }
    ]

    assert result["research"] != ""

    assert result["code"] != ""

    assert result["evaluation"] == (
        "VERDICT: PASS\n"
        "ISSUES: None"
    )

    assert result["human_approval"] == (
        "APPROVE"
    )

    assert result["revision_count"] == 0

    assert result["final_answer"] == (
        "Implementation completed successfully."
    )