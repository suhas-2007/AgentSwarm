from logging.config import fileConfig

import os

from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

from database.connection import Base
from database.models import User, Task


load_dotenv()


config = context.config


if config.config_file_name is not None:

    fileConfig(
        config.config_file_name
    )


DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


if not DATABASE_URL:

    raise RuntimeError(
        "DATABASE_URL is not configured in the .env file."
    )


def get_database_url() -> str:

    if DATABASE_URL.startswith(
        "postgresql+psycopg2://"
    ):

        return DATABASE_URL.replace(
            "postgresql+psycopg2://",
            "postgresql+psycopg://",
            1
        )

    if DATABASE_URL.startswith(
        "postgresql://"
    ):

        return DATABASE_URL.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1
        )

    return DATABASE_URL


target_metadata = Base.metadata


def run_migrations_offline() -> None:

    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        }
    )

    with context.begin_transaction():

        context.run_migrations()


def run_migrations_online() -> None:

    connectable = create_engine(
        get_database_url(),
        poolclass=pool.NullPool
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():

            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():

    run_migrations_offline()

else:

    run_migrations_online()