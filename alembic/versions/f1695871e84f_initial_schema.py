"""initial schema

Revision ID: f1695871e84f
Revises:
Create Date: 2026-09-06 13:52:39.436847

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f1695871e84f"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "tasks",
        sa.Column(
            "current_task_id",
            sa.Integer(),
            nullable=True
        )
    )

    op.add_column(
        "tasks",
        sa.Column(
            "completed_tasks",
            sa.Text(),
            nullable=False,
            server_default="[]"
        )
    )

    op.alter_column(
        "tasks",
        "completed_tasks",
        server_default=None
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "tasks",
        "completed_tasks"
    )

    op.drop_column(
        "tasks",
        "current_task_id"
    )