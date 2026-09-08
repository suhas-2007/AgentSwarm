from typing import TypedDict


class PlanTask(TypedDict, total=False):
    task_id: int
    description: str
    agent: str
    task_type: str
    depends_on: list[int]


class AgentState(TypedDict, total=False):
    task_id: int

    user_goal: str

    plan: str
    plan_tasks: list[PlanTask]

    current_task_id: int | None
    completed_tasks: list[int]

    research: str
    code: str
    content: str
    evaluation: str
    final_answer: str

    revision_count: int

    human_approval: str
    human_feedback: str

    revision_reason: str

    status: str

    api_keys: dict[str, str | None]