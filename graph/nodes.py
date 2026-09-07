from agents.planner import planner_agent
from agents.researcher import researcher_agent
from agents.coder import coder_agent
from agents.content import content_agent
from agents.evaluator import evaluator_agent
from agents.finalizer import finalizer_agent

from artifacts.manager import save_artifact

from graph.state import AgentState

from services.task_control import check_task_stopped


def check_current_task_stopped(
    state: AgentState
) -> None:

    task_id = state.get(
        "task_id"
    )

    if task_id is not None:

        check_task_stopped(
            task_id
        )


def planner_node(
    state: AgentState
) -> AgentState:

    check_current_task_stopped(
        state
    )

    planner_result = planner_agent(
        state["user_goal"]
    )

    check_current_task_stopped(
        state
    )

    plan_tasks = planner_result["tasks"]

    plan = "\n".join(
        f"{task['task_id']}. "
        f"{task['description']} "
        f"[{task['agent']}] "
        f"({task['task_type']})"
        for task in plan_tasks
    )

    return {
        **state,
        "plan": plan,
        "plan_tasks": plan_tasks,
        "current_task_id": None,
        "completed_tasks": [],
        "status": "PLANNING"
    }


def researcher_node(
    state: AgentState
) -> AgentState:

    check_current_task_stopped(
        state
    )

    current_task = get_current_task(
        state
    )

    research = researcher_agent(
        state["user_goal"],
        current_task["description"]
    )

    check_current_task_stopped(
        state
    )

    return {
        **state,
        "research": research,
        "status": "RESEARCHING"
    }


def coder_node(
    state: AgentState
) -> AgentState:

    check_current_task_stopped(
        state
    )

    current_task = get_current_task(
        state
    )

    code = coder_agent(
        state["user_goal"],
        current_task["description"],
        state["research"],
        state["evaluation"],
        state["human_feedback"]
    )

    check_current_task_stopped(
        state
    )

    task_id = state["task_id"]

    save_artifact(
        task_id,
        f"task_{current_task['task_id']}_code.txt",
        code
    )

    return {
        **state,
        "code": code,
        "status": "CODING"
    }


def content_node(
    state: AgentState
) -> AgentState:

    check_current_task_stopped(
        state
    )

    current_task = get_current_task(
        state
    )

    content = content_agent(
        state["user_goal"],
        current_task["description"],
        state["research"],
        state["evaluation"],
        state["human_feedback"]
    )

    check_current_task_stopped(
        state
    )

    return {
        **state,
        "content": content,
        "status": "CREATING_CONTENT"
    }


def evaluator_node(
    state: AgentState
) -> AgentState:

    check_current_task_stopped(
        state
    )

    evaluation_task = get_evaluation_task(
        state
    )

    evaluation = evaluator_agent(
        state["user_goal"],
        evaluation_task,
        state["research"],
        state["code"],
        state["content"]
    )

    check_current_task_stopped(
        state
    )

    return {
        **state,
        "evaluation": evaluation,
        "status": "EVALUATING"
    }


def finalizer_node(
    state: AgentState
) -> AgentState:

    check_current_task_stopped(
        state
    )

    final_answer = finalizer_agent(
        state["user_goal"],
        state["research"],
        state["content"],
        state["code"],
        state["evaluation"]
    )

    check_current_task_stopped(
        state
    )

    return {
        **state,
        "final_answer": final_answer,
        "status": "COMPLETED"
    }


def revision_node(
    state: AgentState
) -> AgentState:

    check_current_task_stopped(
        state
    )

    revision_task = get_revision_task(
        state
    )

    revision_count = (
        state["revision_count"] + 1
    )

    task_agent = revision_task[
        "agent"
    ]

    if task_agent == "researcher":

        research = researcher_agent(
            state["user_goal"],
            revision_task["description"]
        )

        check_current_task_stopped(
            state
        )

        return {
            **state,
            "research": research,
            "revision_count": revision_count,
            "human_feedback": "",
            "revision_reason": "INITIAL",
            "status": "REVISING"
        }

    if task_agent == "coder":

        code = coder_agent(
            state["user_goal"],
            revision_task["description"],
            state["research"],
            state["evaluation"],
            state["human_feedback"]
        )

        check_current_task_stopped(
            state
        )

        save_artifact(
            state["task_id"],
            f"task_{revision_task['task_id']}_revision_{revision_count}_code.txt",
            code
        )

        return {
            **state,
            "code": code,
            "revision_count": revision_count,
            "human_feedback": "",
            "revision_reason": "INITIAL",
            "status": "REVISING"
        }

    if task_agent == "content":

        content = content_agent(
            state["user_goal"],
            revision_task["description"],
            state["research"],
            state["evaluation"],
            state["human_feedback"]
        )

        check_current_task_stopped(
            state
        )

        return {
            **state,
            "content": content,
            "revision_count": revision_count,
            "human_feedback": "",
            "revision_reason": "INITIAL",
            "status": "REVISING"
        }

    raise ValueError(
        f"Unsupported revision agent: "
        f"{task_agent}"
    )


def get_current_task(
    state: AgentState
) -> dict:

    current_task_id = state[
        "current_task_id"
    ]

    if current_task_id is None:

        raise ValueError(
            "No current task is assigned."
        )

    for task in state["plan_tasks"]:

        if task["task_id"] == current_task_id:

            return task

    raise ValueError(
        f"Task {current_task_id} "
        "does not exist in the plan."
    )


def get_revision_task(
    state: AgentState
) -> dict:

    completed_tasks = set(
        state["completed_tasks"]
    )

    worker_tasks = [
        task
        for task in state["plan_tasks"]
        if (
            task["agent"]
            in {
                "researcher",
                "coder",
                "content"
            }
            and task["task_id"]
            in completed_tasks
        )
    ]

    if not worker_tasks:

        raise ValueError(
            "Cannot perform revision because "
            "no completed worker task exists."
        )

    return max(
        worker_tasks,
        key=lambda task: task["task_id"]
    )


def get_evaluation_task(
    state: AgentState
) -> str:

    task_descriptions = [
        (
            f"Task {task['task_id']} "
            f"({task['task_type']}): "
            f"{task['description']}"
        )
        for task in state["plan_tasks"]
    ]

    return "\n".join(
        task_descriptions
    )


def get_next_ready_task(
    state: AgentState
) -> int | None:

    completed = set(
        state["completed_tasks"]
    )

    for task in state["plan_tasks"]:

        task_id = task["task_id"]

        if task_id in completed:

            continue

        dependencies = set(
            task["depends_on"]
        )

        if dependencies.issubset(
            completed
        ):

            return task_id

    return None


def prepare_next_task(
    state: AgentState
) -> AgentState:

    check_current_task_stopped(
        state
    )

    next_task_id = get_next_ready_task(
        state
    )

    if next_task_id is None:

        return {
            **state,
            "current_task_id": None
        }

    return {
        **state,
        "current_task_id": next_task_id
    }


def mark_current_task_complete(
    state: AgentState
) -> AgentState:

    check_current_task_stopped(
        state
    )

    current_task_id = state[
        "current_task_id"
    ]

    if current_task_id is None:

        return state

    completed_tasks = list(
        state["completed_tasks"]
    )

    if current_task_id not in completed_tasks:

        completed_tasks.append(
            current_task_id
        )

    return {
        **state,
        "completed_tasks": completed_tasks,
        "current_task_id": None
    }