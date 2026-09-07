from langgraph.types import interrupt


def human_approval_node(state):

    approval_request = {
        "message": "Human approval is required.",
        "evaluation": state["evaluation"],
        "code": state["code"],
        "revision_count": state["revision_count"]
    }

    human_response = interrupt(
        approval_request
    )

    if human_response.get("approved") is True:

        return {
            **state,
            "human_approval": "APPROVE",
            "human_feedback": "",
            "status": "FINALIZING"
        }

    if human_response.get("approved") is False:

        feedback = human_response.get(
            "feedback",
            ""
        ).strip()

        if not feedback:
            raise ValueError(
                "Feedback is required when rejecting "
                "an implementation."
            )

        return {
            **state,
            "human_approval": "REJECT",
            "human_feedback": feedback,
            "status": "REVISING"
        }

    raise ValueError(
        "Human response must contain "
        "'approved' as true or false."
    )