from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    goal: str = Field(
        ...,
        min_length=1,
        description="The task that AgentSwarm should execute."
    )


class ApprovalRequest(BaseModel):
    approved: bool = Field(
        ...,
        description="Whether the human approves the implementation."
    )

    feedback: str = Field(
        default="",
        description="Feedback provided when rejecting the implementation."
    )