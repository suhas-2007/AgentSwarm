import os

from langchain_google_genai import (
    ChatGoogleGenerativeAI
)

from rag.search import retrieve_documents


def get_llm(api_key: str | None = None):

    key = api_key or os.getenv(
        "GEMINI_API_KEY"
    )

    return ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        google_api_key=key,
        temperature=0
    )


def build_rag_evidence(
    results: list[dict]
) -> str:
    """
    Convert normalized RAG retrieval results
    into evidence that can be provided to
    the Evaluator Agent.
    """

    if not results:

        return (
            "No relevant documentation was "
            "retrieved from the knowledge base."
        )

    evidence_parts = []

    for index, result in enumerate(
        results,
        start=1
    ):

        distance = result.get(
            "distance"
        )

        distance_text = (
            f"{distance:.4f}"
            if distance is not None
            else "unknown"
        )

        evidence_parts.append(
            f"""
Evidence {index}
Source: {result.get("source", "unknown")}
Chunk ID: {result.get("chunk_id", "unknown")}
Document ID: {result.get("id", "unknown")}
Distance: {distance_text}

{result.get("content", "")}
""".strip()
        )

    return "\n\n".join(
        evidence_parts
    )


def evaluator_agent(
    goal: str,
    task_description: str,
    research: str,
    code: str,
    content: str,
    api_key: str | None = None
) -> str:

    query = f"""
Verify the result for this task.

User goal:
{goal}

Task:
{task_description}

Research:
{research}

Look for reliable documentation relevant to:

- factual correctness
- technical correctness
- completeness
- important constraints
- validation
- unsupported claims
- contradictions
"""

    rag_results = retrieve_documents(
        query,
        n_results=3
    )

    evidence = build_rag_evidence(
        rag_results
    )

    implementation_section = (
        code
        if code
        else
        "No code was generated because "
        "the task does not require software "
        "implementation."
    )

    content_section = (
        content
        if content
        else
        "No content output was generated."
    )

    research_section = (
        research
        if research
        else
        "No research output was generated."
    )

    prompt = f"""
You are the Evaluator Agent in AgentSwarm.

Your job is to evaluate the result produced
by the worker agents for the specific task.

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

{research_section}


====================
CONTENT
====================

{content_section}


====================
CODE
====================

{implementation_section}


====================
RAG EVIDENCE
====================

{evidence}


====================
EVALUATION RULES
====================

Evaluate the actual output produced by the
worker agents.

Do NOT require code when the task does not
require code.

For research tasks:

- Check whether useful information was found.
- Check whether important claims are supported.
- Check whether the research is relevant.
- Identify unsupported or speculative claims.

For content tasks:

- Check relevance.
- Check factual consistency with research.
- Check completeness.
- Check whether requested formatting/content
  requirements were followed.

For question tasks:

- Check that questions match the requested topic.
- Check for duplicate questions.
- Check answer correctness when answers are supplied.
- Check explanations when supplied.
- Check factual support.

For coding tasks:

- Check logical correctness.
- Check requirements.
- Check validation.
- Check error handling.
- Check security where relevant.
- Check testing requirements.

RAG evidence verification:

- Compare important factual or technical claims
  against the retrieved evidence.
- Do NOT treat semantic distance as a correctness score.
- Do NOT invent supporting evidence.
- Retrieved evidence may be incomplete.
- Do not claim that evidence supports something
  unless it actually supports the claim.

Claim classification:

SUPPORTED
- Evidence directly supports the claim.

CONTRADICTED
- Evidence conflicts with the claim.

NOT VERIFIED
- Available evidence is insufficient.

A NOT VERIFIED claim is not automatically a reason
for REVISE unless it is an important unsupported
claim that the task requires to be verified.

====================
VERDICT RULE
====================

Return REVISE if there is:

- an important correctness problem
- a missing requirement
- a major unsupported claim
- a contradiction
- a serious security problem
- a significant quality problem

Return PASS if there are no important issues.

Do not require a Coder implementation when
the user's task does not require coding.

====================
OUTPUT FORMAT
====================

VERDICT: PASS or REVISE

CLAIM VERIFICATION:

- Claim: <important claim>
  Status: SUPPORTED / CONTRADICTED / NOT VERIFIED
  Evidence: <source and chunk ID, or None>

Repeat for important claims.

ISSUES:
- List important issues.
- If there are no important issues, write "None".

RECOMMENDATIONS:
- List specific improvements.
- If no improvements are needed, write "None".

EVIDENCE USED:
- Source: <filename>
- Chunk ID: <chunk number>
- Relevance: <why the evidence was useful>

If no relevant evidence was retrieved, write "None".

Do not rewrite the complete output.
"""

    llm = get_llm(api_key=api_key)

    try:

        response = llm.invoke(
            prompt
        )

    except Exception as error:

        error_text = str(error).lower()

        quota_error_terms = [
            "resource_exhausted",
            "resource exhausted",
            "rate limit",
            "rate_limit",
            "quota",
            "429",
            "too many requests"
        ]

        is_quota_error = any(
            term in error_text
            for term in quota_error_terms
        )

        if is_quota_error:

            return """
EVALUATION_UNAVAILABLE

REASON: Gemini evaluator quota has been exhausted.

The worker output was generated, but the Evaluator
could not verify it because the Gemini API returned
a rate-limit or quota error.

The workflow must not treat this result as PASS.
"""

        raise

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