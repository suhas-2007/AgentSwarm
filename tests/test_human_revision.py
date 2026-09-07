import importlib

import graph.human as human
import graph.nodes as nodes
import graph.workflow as workflow_module


def test_human_rejection_triggers_revision(monkeypatch):

    # --------------------------------------------------
    # Fake Planner
    # --------------------------------------------------

    def fake_planner_agent(goal):

        return [
            {
                "task_id": 1,
                "description": "Create the application structure.",
                "agent": "researcher",
                "task_type": "research",
                "depends_on": []
            },
            {
                "task_id": 2,
                "description": "Implement the API endpoints.",
                "agent": "coder",
                "task_type": "coding",
                "depends_on": [1]
            }
        ]

    # --------------------------------------------------
    # Fake Researcher
    # --------------------------------------------------

    def fake_researcher_agent(goal, task_description):

        return (
            "FastAPI supports Pydantic-based request validation."
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

        if human_feedback:

            return (
                "REVISED FastAPI application "
                "with improved error handling."
            )

        return (
            "INITIAL FastAPI application implementation."
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

    human_call_count = 0

    def fake_human_approval_node(state):

        nonlocal human_call_count

        human_call_count += 1

        if human_call_count == 1:

            return {
                **state,
                "human_approval": "REJECT",
                "human_feedback": (
                    "Add better error handling."
                ),
                "status": "REVISING"
            }

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
            "Implementation completed after "
            "human-requested revision."
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
    # Checkpoint configuration
    # --------------------------------------------------

    config = {
        "configurable": {
            "thread_id": "test-human-revision"
        }
    }

    # --------------------------------------------------
    # Execute complete workflow
    # --------------------------------------------------

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
            "description": "Create the application structure.",
            "agent": "researcher",
            "task_type": "research",
            "depends_on": []
        },
        {
            "task_id": 2,
            "description": "Implement the API endpoints.",
            "agent": "coder",
            "task_type": "coding",
            "depends_on": [1]
        }
    ]

    assert result["research"] != ""

    assert result["code"] == (
        "REVISED FastAPI application "
        "with improved error handling."
    )

    assert result["evaluation"] == (
        "VERDICT: PASS\n"
        "ISSUES: None"
    )

    assert result["human_approval"] == (
        "APPROVE"
    )

    assert result["human_feedback"] == ""

    assert result["revision_count"] == 1

    assert result["final_answer"] == (
        "Implementation completed after "
        "human-requested revision."
    )