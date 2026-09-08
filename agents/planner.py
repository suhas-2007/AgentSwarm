import json
import os

from langchain_groq import ChatGroq


ALLOWED_AGENTS = {
    "researcher",
    "coder",
    "content"
}


ALLOWED_TASK_TYPES = {
    "research",
    "coding",
    "content",
    "questions"
}


def get_llm(api_key: str | None = None):

    key = api_key or os.getenv(
        "GROQ_API_KEY"
    )

    return ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=key,
        temperature=0
    )


def planner_agent(
    goal: str,
    api_key: str | None = None
) -> dict:

    llm = get_llm(api_key=api_key)

    prompt = f"""
You are the Planner Agent in AgentSwarm.

Your job is to analyze the user's request and
create the smallest correct sequence of worker
tasks required to complete it.

The available worker agents are:

1. researcher
   - Finds current or reliable information.
   - Performs web research.
   - Useful when the task requires facts,
     current information, sources, documentation,
     technical information, or investigation.

2. coder
   - Creates software/code.
   - Used when the user explicitly asks for
     programming, implementation, debugging,
     algorithms, scripts, applications, APIs,
     or other software.

3. content
   - Creates human-facing non-code output.
   - Used for explanations, summaries, reports,
     study material, questions, MCQs, comparisons,
     answers, and similar content.

The available task types are:

- research
- coding
- content
- questions

IMPORTANT RULES
================

1. Do NOT create evaluator tasks.

2. Do NOT create finalizer tasks.

3. Do NOT create human-review tasks.

The workflow automatically performs evaluation,
human review, revision, and finalization after
worker tasks are completed.

4. Use only these agents:

   researcher
   coder
   content

5. Use only these task types:

   research
   coding
   content
   questions

6. A research task MUST use researcher.

7. A coding task MUST use coder.

8. A content task MUST use content.

9. A questions task MUST use content.

10. If the user's request requires current,
    recent, latest, live, or externally verified
    information, use researcher.

11. If the user asks to create content based on
    information that must first be researched,
    create a researcher task followed by a
    content task.

12. If the user asks for questions about a topic
    that requires current or researched information,
    create a researcher task followed by a
    questions task.

13. If the user asks for coding that requires
    external technical information, create a
    researcher task followed by a coding task.

14. If coding can be completed without external
    research, a coder task may be sufficient.

15. If the user asks only for an explanation of
    information that does not require current
    research, content may be sufficient.

16. Do not create unnecessary tasks.

17. Every dependency must refer to an earlier task.

18. Task IDs must start at 1 and increase
    sequentially.

19. Return at least one task.

20. Return JSON only.

JSON FORMAT
===========

Return exactly this structure:

{{
    "tasks": [
        {{
            "task_id": 1,
            "description": "Specific task description",
            "agent": "researcher",
            "task_type": "research",
            "depends_on": []
        }}
    ]
}}

The description must clearly explain what that
specific worker needs to accomplish.

Do not include Markdown.

Do not include explanations outside the JSON.

USER REQUEST
============

{goal}
"""

    response = llm.invoke(prompt)

    content = response.content

    if isinstance(content, list):

        content = "\n".join(
            item["text"]
            for item in content
            if isinstance(item, dict)
            and "text" in item
        )

    content = content.strip()

    if content.startswith("```"):

        lines = content.splitlines()

        if lines:

            lines = lines[1:]

        if lines and lines[-1].strip() == "```":

            lines = lines[:-1]

        content = "\n".join(lines).strip()

    try:

        plan = json.loads(content)

    except json.JSONDecodeError as error:

        raise ValueError(
            f"Planner returned invalid JSON: {error}"
        )


    if not isinstance(plan, dict):

        raise ValueError(
            "Planner response must be a JSON object."
        )


    tasks = plan.get("tasks")


    if not isinstance(tasks, list):

        raise ValueError(
            "Planner response must contain a tasks list."
        )


    if not tasks:

        raise ValueError(
            "Planner must create at least one task."
        )


    validated_tasks = []


    expected_task_id = 1


    for task in tasks:

        if not isinstance(task, dict):

            raise ValueError(
                "Every planner task must be an object."
            )


        task_id = task.get(
            "task_id"
        )

        description = task.get(
            "description"
        )

        agent = task.get(
            "agent"
        )

        task_type = task.get(
            "task_type"
        )

        depends_on = task.get(
            "depends_on",
            []
        )


        if task_id != expected_task_id:

            raise ValueError(
                "Planner task IDs must be sequential "
                "starting from 1."
            )


        if not isinstance(
            description,
            str
        ) or not description.strip():

            raise ValueError(
                f"Task {task_id} must have a description."
            )


        if agent not in ALLOWED_AGENTS:

            raise ValueError(
                f"Task {task_id} uses invalid agent: "
                f"{agent}"
            )


        if task_type not in ALLOWED_TASK_TYPES:

            raise ValueError(
                f"Task {task_id} uses invalid task type: "
                f"{task_type}"
            )


        expected_agent = {
            "research": "researcher",
            "coding": "coder",
            "content": "content",
            "questions": "content"
        }[task_type]


        if agent != expected_agent:

            raise ValueError(
                f"Task {task_id} has incompatible "
                f"agent '{agent}' for task type "
                f"'{task_type}'. Expected "
                f"'{expected_agent}'."
            )


        if not isinstance(
            depends_on,
            list
        ):

            raise ValueError(
                f"Task {task_id} dependencies "
                f"must be a list."
            )


        for dependency in depends_on:

            if not isinstance(
                dependency,
                int
            ):

                raise ValueError(
                    f"Task {task_id} contains an "
                    f"invalid dependency."
                )


            if dependency >= task_id:

                raise ValueError(
                    f"Task {task_id} can only depend "
                    f"on earlier tasks."
                )


            if dependency < 1:

                raise ValueError(
                    f"Task {task_id} contains an "
                    f"invalid dependency ID."
                )


        validated_tasks.append(
            {
                "task_id": task_id,
                "description": description.strip(),
                "agent": agent,
                "task_type": task_type,
                "depends_on": depends_on
            }
        )


        expected_task_id += 1


    return {
        "tasks": validated_tasks
    }