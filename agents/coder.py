import os

from langchain_groq import ChatGroq


def get_llm():

    return ChatGroq(
        model="openai/gpt-oss-120b",
        groq_api_key=os.getenv(
            "GROQ_API_KEY"
        ),
        temperature=0
    )


def coder_agent(
    goal: str,
    task_description: str,
    research: str,
    evaluation: str,
    human_feedback: str
) -> str:

    llm = get_llm()

    previous_evaluation = (
        evaluation
        if evaluation
        else
        "No previous evaluation. "
        "This is the first implementation."
    )

    previous_human_feedback = (
        human_feedback
        if human_feedback
        else
        "No human feedback."
    )

    prompt = f"""
You are the Coder Agent in AgentSwarm.

Your responsibility is to implement the
specific task assigned by the Planner.

====================
USER GOAL
====================

{goal}


====================
CURRENT TASK
====================

{task_description}


====================
RESEARCH
====================

{research}


====================
PREVIOUS EVALUATOR FEEDBACK
====================

{previous_evaluation}


====================
HUMAN FEEDBACK
====================

{previous_human_feedback}


====================
IMPLEMENTATION RULES
====================

Implement the current task based on the
research and requirements.

If this is a revision:

- Carefully examine the evaluator feedback.
- Carefully examine the human feedback.
- Fix every important issue identified.
- Preserve parts of the implementation that
  are already correct.
- Do not introduce unnecessary changes.

Requirements:

- Produce clean, practical code.
- Follow the recommended technologies.
- Organize the implementation logically.
- Include important error handling.
- Address the human's requested changes.
- Do not rewrite unrelated parts of the project.
- Do not explain the code before the implementation.

Return the implementation with filenames
and code blocks.
"""

    response = llm.invoke(
        prompt
    )

    if isinstance(
        response.content,
        list
    ):

        return "\n".join(
            item["text"]
            for item in response.content
            if isinstance(item, dict)
            and "text" in item
        )

    return response.content