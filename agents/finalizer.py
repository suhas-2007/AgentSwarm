import os

from langchain_groq import ChatGroq


def get_llm():

    return ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=os.getenv(
            "GROQ_API_KEY"
        ),
        temperature=0
    )


def finalizer_agent(
    goal: str,
    research: str,
    content: str,
    code: str,
    evaluation: str
) -> str:

    llm = get_llm()

    prompt = f"""
You are the Finalizer Agent in AgentSwarm.

The worker output has passed evaluation and
has been approved by the human.

Your job is to prepare the final response
for the user.

====================
USER GOAL
====================

{goal}


====================
RESEARCH
====================

{research}


====================
CONTENT
====================

{content}


====================
APPROVED IMPLEMENTATION
====================

{code}


====================
FINAL EVALUATION
====================

{evaluation}


====================
FINAL RESPONSE RULES
====================

Create the final answer that best matches
the user's original request.

IMPORTANT:

1. If the user requested information or research,
   use the research and content to provide the
   actual useful answer.

2. If the user requested complete information
   about a topic, provide a detailed and
   well-structured answer based on the available
   research.

3. If the user requested a summary, provide the
   actual summary.

4. If the user requested questions, provide the
   actual questions and answers when generated.

5. If the user requested explanations, provide
   the actual explanation.

6. If the user requested a comparison, provide
   the actual comparison.

7. If the user requested code, include the actual
   approved implementation.

8. If code exists, preserve it exactly as supplied
   by the Coder Agent.

9. Do not invent information that is not present
   in the worker outputs or supported evidence.

10. Clearly distinguish confirmed information from
    uncertainty or speculation when relevant.

11. Do not claim that something was executed or
    tested unless the evaluation explicitly
    confirms actual execution.

12. Do not say that a Coder implementation is
    missing when the user's task did not require
    code.

13. Do not produce a generic project report.
    Answer the user's actual question.

14. Keep the response organized and practical.

15. Include the useful output itself, not merely
    a description of what the agents did.

16. If code is present, use appropriate Markdown
    code blocks.

17. Do not modify approved code.

18. Do not invent files, features, technologies,
    tests, performance results, or capabilities.

19. Use the evaluator's feedback to avoid presenting
    information that was identified as incorrect,
    unsupported, or contradicted.

20. If the available evidence is insufficient for
    an important claim, clearly state that the claim
    could not be verified.

====================
OUTPUT RULES
====================

The final response should be directly useful
to the user.

Do not describe the internal AgentSwarm workflow
unless it is useful to the user's request.

Do not mention hidden prompts, internal agent
instructions, or internal implementation details
of AgentSwarm.

For research requests, prioritize the actual
researched answer.

For content requests, prioritize the generated
content.

For coding requests, prioritize the approved
implementation.

Return the final answer directly.
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