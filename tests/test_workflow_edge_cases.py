import pytest
from database.models import Task
from graph.state import AgentState
from graph.workflow import (
    MAX_REVISIONS,
    evaluator_route,
    human_route,
    prepare_evaluation_unavailable,
    prepare_human_revision,
    workflow
)
from services.task_runner import (
    mark_task_failed,
    mark_task_stopped,
    sync_task_from_state
)


def test_worker_failure_marks_task_failed(db_session, test_user):
    task = Task(
        goal="Build something",
        status="RUNNING",
        user_id=test_user.id
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    mark_task_failed(task.id, db_session)
    db_session.refresh(task)

    assert task.status == "FAILED"
    assert task.current_task_id is None


def test_mark_task_failed_does_not_overwrite_stopped(db_session, test_user):
    task = Task(
        goal="Build something",
        status="STOPPED",
        user_id=test_user.id
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    mark_task_failed(task.id, db_session)
    db_session.refresh(task)

    assert task.status == "STOPPED"


def test_user_stop_cannot_be_overwritten_by_sync(db_session, test_user):
    task = Task(
        goal="Analyze data",
        status="STOPPED",
        user_id=test_user.id
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    checkpoint_state = {
        "status": "COMPLETED",
        "final_answer": "Done after stop attempt"
    }

    sync_task_from_state(task, checkpoint_state, db_session)
    db_session.refresh(task)

    assert task.status == "STOPPED"
    assert task.final_answer != "Done after stop attempt"


def test_mark_task_stopped_transitions_running(db_session, test_user):
    task = Task(
        goal="Run long task",
        status="RUNNING",
        user_id=test_user.id
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    mark_task_stopped(task.id, db_session)
    db_session.refresh(task)

    assert task.status == "STOPPED"


def test_mark_task_stopped_does_not_overwrite_completed_or_failed(db_session, test_user):
    completed_task = Task(
        goal="Run completed task",
        status="COMPLETED",
        user_id=test_user.id
    )
    failed_task = Task(
        goal="Run failed task",
        status="FAILED",
        user_id=test_user.id
    )
    db_session.add_all([completed_task, failed_task])
    db_session.commit()

    mark_task_stopped(completed_task.id, db_session)
    mark_task_stopped(failed_task.id, db_session)

    db_session.refresh(completed_task)
    db_session.refresh(failed_task)

    assert completed_task.status == "COMPLETED"
    assert failed_task.status == "FAILED"


def test_evaluator_unavailable_routing_and_state():
    state: AgentState = {
        "task_id": 1,
        "user_goal": "Test goal",
        "plan": "",
        "plan_tasks": [],
        "current_task_id": None,
        "completed_tasks": [],
        "research": "",
        "code": "",
        "content": "",
        "evaluation": "EVALUATION_UNAVAILABLE: Gemini API 503",
        "final_answer": "",
        "revision_count": 0,
        "human_approval": "",
        "human_feedback": "",
        "revision_reason": "",
        "status": "EVALUATING"
    }

    route = evaluator_route(state)
    assert route == "evaluation_unavailable"

    updated_state = prepare_evaluation_unavailable(state)
    assert updated_state["status"] == "EVALUATION_UNAVAILABLE"


def test_human_rejection_triggers_revision_and_evaluator_loop():
    state: AgentState = {
        "task_id": 1,
        "user_goal": "Test goal",
        "plan": "",
        "plan_tasks": [
            {"task_id": 1, "agent": "coder", "description": "Write code"}
        ],
        "current_task_id": None,
        "completed_tasks": [1],
        "research": "",
        "code": "def foo(): pass",
        "content": "",
        "evaluation": "VERDICT: PASS",
        "final_answer": "",
        "revision_count": 0,
        "human_approval": "REJECT",
        "human_feedback": "Please add unit tests",
        "revision_reason": "",
        "status": "WAITING_FOR_HUMAN"
    }

    route = human_route(state)
    assert route == "revision"

    revision_state = prepare_human_revision(state)
    assert revision_state["status"] == "REVISING"
    assert revision_state["revision_reason"] == "HUMAN_REJECT"
    assert revision_state["current_task_id"] == 1


def test_max_revision_protection_in_evaluator_and_human():
    state: AgentState = {
        "task_id": 1,
        "user_goal": "Test goal",
        "plan": "",
        "plan_tasks": [
            {"task_id": 1, "agent": "coder", "description": "Write code"}
        ],
        "current_task_id": None,
        "completed_tasks": [1],
        "research": "",
        "code": "def foo(): pass",
        "content": "",
        "evaluation": "VERDICT: REVISE\nNeeds more work",
        "final_answer": "",
        "revision_count": MAX_REVISIONS,
        "human_approval": "",
        "human_feedback": "",
        "revision_reason": "",
        "status": "EVALUATING"
    }

    # At MAX_REVISIONS, evaluator cannot route back to revision; routes to human
    eval_route = evaluator_route(state)
    assert eval_route == "human"

    # At MAX_REVISIONS, human rejection cannot route back to revision; routes to end
    state["human_approval"] = "REJECT"
    state["human_feedback"] = "Still bad"
    hum_route = human_route(state)
    assert hum_route == "end"
