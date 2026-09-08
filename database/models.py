from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from database.connection import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    google_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True
    )

    auth_provider: Mapped[str] = mapped_column(
        String(50),
        default="local",
        nullable=False
    )

    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    gemini_api_key: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    groq_api_key: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    tavily_api_key: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    reset_token_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    reset_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    goal: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="STARTING"
    )

    plan: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False
    )

    research: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False
    )

    code: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False
    )

    evaluation: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False
    )

    final_answer: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False
    )

    revision_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    current_task_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    completed_tasks: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="tasks"
    )

    shares: Mapped[list["TaskShare"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan"
    )


class TaskShare(Base):
    __tablename__ = "task_shares"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id"),
        nullable=False,
        index=True
    )

    token: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    task: Mapped["Task"] = relationship(
        back_populates="shares"
    )