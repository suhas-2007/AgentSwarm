import json

from database.models import Task
from services.task_runner import sync_task_from_state


class FakeDB:
    def __init__(self):
        self.commit_count = 0
        self.refresh_count = 0

    def commit(self):
        self.commit_count += 1

    def refresh(self, task):
        self.refresh_count += 1


def create_task():
    task = Task()

    task.status = "RUNNING"
    task.plan = ""
    task.research = ""
    task.content = ""
    task.code = ""
    task.evaluation = ""
    task.final_answer = ""
    task.revision_count = 0
    task.current_task_id = None
    task.completed_tasks = "[]"

    return task


def test_normal_sync():
    print("\n[1] Testing normal state synchronization...")

    task = create_task()
    db = FakeDB()

    state = {
        "status": "CODING",
        "plan": "1. Build application",
        "research": "Research completed",
        "content": "Content completed",
        "code": "print('hello')",
        "evaluation": "",
        "final_answer": "",
        "revision_count": 0,
        "current_task_id": 2,
        "completed_tasks": [1],
    }

    sync_task_from_state(
        task,
        state,
        db
    )

    assert task.status == "CODING"
    assert task.plan == "1. Build application"
    assert task.research == "Research completed"
    assert task.content == "Content completed"
    assert task.code == "print('hello')"
    assert task.current_task_id == 2
    assert task.revision_count == 0

    assert json.loads(
        task.completed_tasks
    ) == [1]

    assert db.commit_count == 1
    assert db.refresh_count == 1

    print("PASS: normal synchronization")


def test_completed_sync():
    print("\n[2] Testing completed workflow synchronization...")

    task = create_task()
    db = FakeDB()

    state = {
        "status": "COMPLETED",
        "plan": "Complete plan",
        "research": "Complete research",
        "content": "Complete content",
        "code": "Complete code",
        "evaluation": "VERDICT: PASS",
        "final_answer": "Final answer",
        "revision_count": 1,
        "current_task_id": None,
        "completed_tasks": [1, 2, 3],
    }

    sync_task_from_state(
        task,
        state,
        db
    )

    assert task.status == "COMPLETED"
    assert task.final_answer == "Final answer"
    assert task.evaluation == "VERDICT: PASS"
    assert task.revision_count == 1
    assert task.current_task_id is None

    assert json.loads(
        task.completed_tasks
    ) == [1, 2, 3]

    print("PASS: completed synchronization")


def test_evaluation_unavailable_sync():
    print("\n[3] Testing evaluator-unavailable synchronization...")

    task = create_task()
    db = FakeDB()

    state = {
        "status": "EVALUATION_UNAVAILABLE",
        "evaluation": (
            "EVALUATION_UNAVAILABLE\n\n"
            "REASON: Gemini evaluator quota has been exhausted."
        ),
        "completed_tasks": [1, 2],
        "revision_count": 0,
        "current_task_id": None,
    }

    sync_task_from_state(
        task,
        state,
        db
    )

    assert task.status == "EVALUATION_UNAVAILABLE"

    assert "EVALUATION_UNAVAILABLE" in (
        task.evaluation
    )

    assert json.loads(
        task.completed_tasks
    ) == [1, 2]

    print("PASS: evaluator-unavailable synchronization")


def test_stopped_task_is_protected():
    print("\n[4] Testing STOPPED task protection...")

    task = create_task()

    task.status = "STOPPED"
    task.code = "Original code"

    db = FakeDB()

    state = {
        "status": "COMPLETED",
        "code": "Late workflow code",
        "final_answer": "Late answer",
        "completed_tasks": [1, 2],
    }

    sync_task_from_state(
        task,
        state,
        db
    )

    assert task.status == "STOPPED"

    assert task.code == "Original code"

    assert db.commit_count == 0

    print("PASS: STOPPED task protection")


def test_partial_state_preserves_existing_values():
    print("\n[5] Testing partial state preservation...")

    task = create_task()

    task.plan = "Existing plan"
    task.code = "Existing code"
    task.final_answer = "Existing answer"

    db = FakeDB()

    state = {
        "status": "RESEARCHING",
        "research": "New research",
    }

    sync_task_from_state(
        task,
        state,
        db
    )

    assert task.status == "RESEARCHING"

    assert task.plan == "Existing plan"
    assert task.code == "Existing code"
    assert task.final_answer == "Existing answer"

    assert task.research == "New research"

    print("PASS: partial state preservation")


def run_tests():
    print("=" * 60)
    print("AgentSwarm Task Synchronization Tests")
    print("=" * 60)

    test_normal_sync()
    test_completed_sync()
    test_evaluation_unavailable_sync()
    test_stopped_task_is_protected()
    test_partial_state_preserves_existing_values()

    print()
    print("=" * 60)
    print("ALL TASK SYNCHRONIZATION TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()