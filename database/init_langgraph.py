import os

from dotenv import load_dotenv
from psycopg import connect
from psycopg.rows import dict_row

from langgraph.checkpoint.postgres import PostgresSaver


load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not configured."
    )


def get_psycopg_url() -> str:

    if DATABASE_URL.startswith(
        "postgresql+psycopg2://"
    ):
        return DATABASE_URL.replace(
            "postgresql+psycopg2://",
            "postgresql://",
            1
        )

    if DATABASE_URL.startswith(
        "postgresql+psycopg://"
    ):
        return DATABASE_URL.replace(
            "postgresql+psycopg://",
            "postgresql://",
            1
        )

    return DATABASE_URL


def init_langgraph_checkpoint():

    psycopg_url = get_psycopg_url()

    connection = connect(
        psycopg_url,
        autocommit=True,
        row_factory=dict_row
    )

    try:

        checkpointer = PostgresSaver(
            connection
        )

        checkpointer.setup()

        print(
            "LANGGRAPH POSTGRES CHECKPOINT TABLES "
            "INITIALIZED SUCCESSFULLY"
        )

    finally:

        connection.close()


if __name__ == "__main__":

    init_langgraph_checkpoint()