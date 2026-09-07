import os

from dotenv import load_dotenv

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import StateGraph, START, END

from psycopg import connect
from psycopg.rows import dict_row

from graph.state import AgentState

from graph.nodes import (
    planner_node,
    researcher_node,
    coder_node,
    content_node,
    evaluator_node,
    finalizer_node,
    revision_node,
    prepare_next_task,
    mark_current_task_complete
)

from graph.human import human_approval_node


load_dotenv()


MAX_REVISIONS = 2


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


if not DATABASE_URL:

    raise ValueError(
        "DATABASE_URL is not configured."
    )


def get_psycopg_url() -> str:

    if DATABASE_URL.startswith(
        "postgresql+psycopg2://"
    ):

        return DATABASE_URL.replace(
            "postgresql+psycopg2://",
            "postgresql://",
            1
        )

    if DATABASE_URL.startswith(
        "postgresql+psycopg://"
    ):

        return DATABASE_URL.replace(
            "postgresql+psycopg://",
            "postgresql://",
            1
        )

    return DATABASE_URL


# =========================================================
# TASK ROUTER
# =========================================================

def task_router(
    state: AgentState
) -> str:

    current_task_id = state[
        "current_task_id"
    ]

    if current_task_id is None:

        return "evaluator"

    for task in state["plan_tasks"]:

        if task["task_id"] == current_task_id:

            return task["agent"]

    raise ValueError(
        f"Task {current_task_id} "
        "does not exist in the plan."
    )


# =========================================================
# EVALUATOR ROUTING
# =========================================================

def evaluator_route(
    state: AgentState
) -> str:

    evaluation = (
        state["evaluation"]
        .upper()
    )

    if (
        "EVALUATION_UNAVAILABLE"
        in evaluation
    ):

        return "evaluation_unavailable"

    if (
        "VERDICT: REVISE"
        in evaluation
        and state["revision_count"]
        < MAX_REVISIONS
    ):

        return "revision"

    return "human"


# =========================================================
# HUMAN ROUTING
# =========================================================

def human_route(
    state: AgentState
) -> str:

    if (
        state["human_approval"]
        == "APPROVE"
    ):

        return "finalizer"

    if (
        state["human_approval"]
        == "REJECT"
        and state["revision_count"]
        < MAX_REVISIONS
    ):

        return "revision"

    return "end"


# =========================================================
# REVISION PREPARATION
# =========================================================

def prepare_evaluator_revision(
    state: AgentState
) -> AgentState:

    revision_task = (
        get_revision_task_for_workflow(
            state
        )
    )

    return {
        **state,

        "current_task_id":
            revision_task["task_id"],

        "revision_reason":
            "EVALUATOR_REVISE",

        "status":
            "REVISING"
    }


def prepare_human_revision(
    state: AgentState
) -> AgentState:

    revision_task = (
        get_revision_task_for_workflow(
            state
        )
    )

    return {
        **state,

        "current_task_id":
            revision_task["task_id"],

        "revision_reason":
            "HUMAN_REJECT",

        "status":
            "REVISING"
    }


def get_revision_task_for_workflow(
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
            "Cannot revise because no completed "
            "worker task exists."
        )

    return max(
        worker_tasks,
        key=lambda task:
            task["task_id"]
    )


# =========================================================
# HUMAN APPROVAL PREPARATION
# =========================================================

def prepare_human_approval(
    state: AgentState
) -> AgentState:

    return {
        **state,

        "status":
            "WAITING_FOR_HUMAN"
    }


# =========================================================
# EVALUATION UNAVAILABLE
# =========================================================

def prepare_evaluation_unavailable(
    state: AgentState
) -> AgentState:

    return {
        **state,

        "status":
            "EVALUATION_UNAVAILABLE"
    }


# =========================================================
# BUILD LANGGRAPH WORKFLOW
# =========================================================

workflow = StateGraph(
    AgentState
)


workflow.add_node(
    "planner",
    planner_node
)


workflow.add_node(
    "prepare_next_task",
    prepare_next_task
)


workflow.add_node(
    "researcher",
    researcher_node
)


workflow.add_node(
    "coder",
    coder_node
)


workflow.add_node(
    "content",
    content_node
)


workflow.add_node(
    "evaluator",
    evaluator_node
)


workflow.add_node(
    "mark_current_task_complete",
    mark_current_task_complete
)


workflow.add_node(
    "prepare_human_approval",
    prepare_human_approval
)


workflow.add_node(
    "prepare_evaluation_unavailable",
    prepare_evaluation_unavailable
)


workflow.add_node(
    "human",
    human_approval_node
)


workflow.add_node(
    "prepare_evaluator_revision",
    prepare_evaluator_revision
)


workflow.add_node(
    "prepare_human_revision",
    prepare_human_revision
)


workflow.add_node(
    "revision",
    revision_node
)


workflow.add_node(
    "finalizer",
    finalizer_node
)


# =========================================================
# START → PLANNER
# =========================================================

workflow.add_edge(
    START,
    "planner"
)


# =========================================================
# PLANNER → SCHEDULER
# =========================================================

workflow.add_edge(
    "planner",
    "prepare_next_task"
)


# =========================================================
# SCHEDULER → WORKER / EVALUATOR
# =========================================================

workflow.add_conditional_edges(
    "prepare_next_task",
    task_router,
    {
        "researcher":
            "researcher",

        "coder":
            "coder",

        "content":
            "content",

        "evaluator":
            "evaluator"
    }
)


# =========================================================
# WORKERS → MARK TASK COMPLETE
# =========================================================

workflow.add_edge(
    "researcher",
    "mark_current_task_complete"
)


workflow.add_edge(
    "coder",
    "mark_current_task_complete"
)


workflow.add_edge(
    "content",
    "mark_current_task_complete"
)


# =========================================================
# TASK COMPLETION → NEXT TASK
# =========================================================

workflow.add_edge(
    "mark_current_task_complete",
    "prepare_next_task"
)


# =========================================================
# EVALUATOR ROUTING
# =========================================================

workflow.add_conditional_edges(
    "evaluator",
    evaluator_route,
    {
        "revision":
            "prepare_evaluator_revision",

        "human":
            "prepare_human_approval",

        "evaluation_unavailable":
            "prepare_evaluation_unavailable"
    }
)


# =========================================================
# EVALUATOR REVISION → WORKER
# =========================================================

workflow.add_edge(
    "prepare_evaluator_revision",
    "revision"
)


# =========================================================
# EVALUATION UNAVAILABLE → END
# =========================================================

workflow.add_edge(
    "prepare_evaluation_unavailable",
    END
)


# =========================================================
# HUMAN APPROVAL PREPARATION → HUMAN
# =========================================================

workflow.add_edge(
    "prepare_human_approval",
    "human"
)


# =========================================================
# HUMAN ROUTING
# =========================================================

workflow.add_conditional_edges(
    "human",
    human_route,
    {
        "revision":
            "prepare_human_revision",

        "finalizer":
            "finalizer",

        "end":
            END
    }
)


# =========================================================
# HUMAN REVISION → WORKER
# =========================================================

workflow.add_edge(
    "prepare_human_revision",
    "revision"
)


# =========================================================
# REVISION → EVALUATOR
# =========================================================

workflow.add_edge(
    "revision",
    "evaluator"
)


# =========================================================
# FINALIZER
# =========================================================

workflow.add_edge(
    "finalizer",
    END
)


# =========================================================
# POSTGRESQL LANGGRAPH CHECKPOINTER
# =========================================================

psycopg_url = get_psycopg_url()


checkpoint_connection = connect(
    psycopg_url,
    autocommit=True,
    row_factory=dict_row
)


checkpointer = PostgresSaver(
    checkpoint_connection
)


# =========================================================
# COMPILE WORKFLOW
# =========================================================

app = workflow.compile(
    checkpointer=checkpointer
)