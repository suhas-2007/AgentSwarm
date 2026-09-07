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


def content_agent(
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
        "This is the first content generation."
    )

    previous_human_feedback = (
        human_feedback
        if human_feedback
        else
        "No human feedback."
    )

    prompt = f"""
You are the Content Agent in AgentSwarm.

Your responsibility is to create accurate,
useful human-facing content for the specific
task assigned by the Planner.

The task may be an explanation, summary, report,
study material, question set, comparison, or
another non-code content task.

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
PREVIOUS EVALUATION
====================

{previous_evaluation}

====================
HUMAN FEEDBACK
====================

{previous_human_feedback}

====================
GENERAL CONTENT RULES
====================

Create the actual content requested by the user.

Use the supplied research when it is relevant.

Do not invent factual claims when the research
does not support them.

When reliable information is unavailable:
- clearly state the limitation
- do not present guesses as facts

When sources or research contain uncertainty
or conflicting information:
- preserve the uncertainty
- do not silently turn uncertain information
  into a definite claim

Keep the content relevant to the assigned task.

Do not produce a generic AgentSwarm report.

====================
EXPLANATIONS
====================

For explanation requests:

- explain the requested topic directly
- organize complex information into clear sections
- define important terms
- include useful examples when appropriate
- avoid unnecessary information

====================
SUMMARIES
====================

For summary requests:

- preserve the important information
- remove unnecessary repetition
- do not introduce information that was not
  present in the supplied material or research
- match the requested level of detail

====================
QUESTIONS
====================

For question-generation tasks:

Create questions that are directly relevant
to the requested topic.

Follow the requested number of questions.

Avoid duplicate or nearly duplicate questions.

If multiple-choice questions are requested:

- provide clear question wording
- provide answer choices
- provide the correct answer
- make distractors plausible
- avoid ambiguous questions

If answers are requested:

- provide the answer for every question

If explanations are requested:

- provide an explanation for every answer

Do not create questions based on unsupported
facts.

If the task concerns current or recent information,
use the supplied research as the factual basis.

====================
COMPARISONS
====================

For comparison tasks:

- identify the requested subjects
- compare relevant properties
- clearly show important differences
- mention similarities when useful
- avoid unsupported rankings

====================
REVISION
====================

If this is a revision:

- examine the evaluator feedback
- examine human feedback
- fix the identified problems
- preserve correct existing content
- do not introduce unnecessary changes
- make the result better aligned with the
  original task

====================
OUTPUT
====================

Return the requested content directly.

Do not explain these instructions.

Do not describe the internal AgentSwarm workflow.

Do not say what you would generate.

Generate the actual requested content.
"""

    response = llm.invoke(prompt)

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