from tools.web_search import web_search


def researcher_agent(
    goal: str,
    task_description: str
) -> str:

    search_query = (
        f"{goal}. "
        f"Research specifically: {task_description}"
    )

    search_query = " ".join(
        search_query.split()
    )

    search_results = web_search(
        search_query
    )

    research = f"""
Research collected by the Research Agent.

====================
USER GOAL
====================

{goal}

====================
CURRENT TASK
====================

{task_description}

====================
RESEARCH RESULTS
====================

{search_results}

====================
RESEARCH USAGE
====================

The information above was collected specifically
for the current research task.

Downstream agents should use these findings as
evidence and should avoid treating unsupported
claims as verified facts.
"""

    return research