import json

from database.models import Task
from services.task_runner import sync_task_from_state


class FakeResult:
    def __init__(self, rowcount):
        self.rowcount = rowcount


class FakeDB:
    def __init__(self):
        self.committed = False
        self.refreshed_objects = []

    def execute(self, statement):
        """
        Simulate the SQLAlchemy UPDATE used by
        sync_task_from_state().

        The statement contains the STOPPED protection
        condition. For these tests, we reproduce the
        important behavior against the fake Task object.
        """

        task_id = statement._where_criteria[0].right.value

        assert task_id is not None

        # Determine whether the UPDATE is allowed.
        if hasattr(self, "task") and self.task.status == "STOPPED":
            return FakeResult(0)

        values = statement._values

        for column, value in values.items():

            column_name = column.key

            # SQLAlchemy may wrap literal values.
            if hasattr(value, "value"):
                value = value.value

            setattr(
                self.task,
                column_name,
                value
            )

        return FakeResult(1)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        self.refreshed_objects.append(obj)

    def scalar(self, statement):
        return None


def create_task():
    task = Task(
        id=1,
        user_id=1,
        goal="Test task",
        status="STARTING",
        plan="",
        research="",
        content="",
        code="",
        evaluation="",
        final_answer="",
        revision_count=0,
        current_task_id=None,
        completed_tasks=json.dumps([])
    )

    return task


def prepare_db(db, task):
    db.task = task
    return db


def test_normal_sync():

    print(
        "\n[1] Testing normal state synchronization..."
    )

    task = create_task()

    db = prepare_db(
        FakeDB(),
        task
    )

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
    assert task.completed_tasks == json.dumps([1])
    assert db.committed is True


def test_completed_sync():

    print(
        "\n[2] Testing completed workflow synchronization..."
    )

    task = create_task()

    db = prepare_db(
        FakeDB(),
        task
    )

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
    assert task.plan == "Complete plan"
    assert task.research == "Complete research"
    assert task.content == "Complete content"
    assert task.code == "Complete code"
    assert task.evaluation == "VERDICT: PASS"
    assert task.final_answer == "Final answer"
    assert task.revision_count == 1
    assert task.current_task_id is None
    assert task.completed_tasks == json.dumps(
        [1, 2, 3]
    )


def test_evaluation_unavailable_sync():

    print(
        "\n[3] Testing evaluator-unavailable synchronization..."
    )

    task = create_task()

    db = prepare_db(
        FakeDB(),
        task
    )

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

    assert task.evaluation == (
        "EVALUATION_UNAVAILABLE\n\n"
        "REASON: Gemini evaluator quota has been exhausted."
    )

    assert task.completed_tasks == json.dumps(
        [1, 2]
    )


def test_stopped_task_is_protected():

    print(
        "\n[4] Testing STOPPED task protection..."
    )

    task = create_task()

    task.status = "STOPPED"
    task.code = "Original code"

    db = prepare_db(
        FakeDB(),
        task
    )

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
    assert task.final_answer == ""


def test_partial_state_preserves_existing_values():

    print(
        "\n[5] Testing partial state preservation..."
    )

    task = create_task()

    task.plan = "Existing plan"
    task.code = "Existing code"
    task.final_answer = "Existing answer"

    db = prepare_db(
        FakeDB(),
        task
    )

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
    assert task.research == "New research"

    assert task.plan == "Existing plan"
    assert task.code == "Existing code"
    assert task.final_answer == "Existing answer"