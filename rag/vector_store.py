import os
from pathlib import Path

import chromadb


# Create a stable local persistent ChromaDB database.
# By default it is stored inside the project's rag/chroma_db
# directory, regardless of the process's current working directory.
DEFAULT_DB_PATH = (
    Path(__file__).resolve().parent / "chroma_db"
)

CHROMA_DB_PATH = Path(
    os.getenv(
        "CHROMA_DB_PATH",
        str(DEFAULT_DB_PATH)
    )
).resolve()

client = chromadb.PersistentClient(
    path=str(CHROMA_DB_PATH)
)


COLLECTION_NAME = "agent_knowledge"


def get_collection():
    """
    Get the ChromaDB collection used by AgentSwarm.
    """

    return client.get_or_create_collection(
        name=COLLECTION_NAME
    )


def add_documents(
    documents: list[str],
    ids: list[str],
    metadatas: list[dict]
):
    """
    Add document chunks and their metadata to ChromaDB.
    """

    if not (
        len(documents)
        == len(ids)
        == len(metadatas)
    ):

        raise ValueError(
            "documents, ids, and metadatas "
            "must contain the same number of items."
        )

    if not documents:

        return

    collection = get_collection()

    collection.add(
        documents=documents,
        ids=ids,
        metadatas=metadatas
    )


def search_documents(
    query: str,
    n_results: int = 3
):
    """
    Search the knowledge base using semantic similarity.
    """

    if not isinstance(query, str):

        raise TypeError(
            "query must be a string."
        )

    query = query.strip()

    if not query:

        raise ValueError(
            "query cannot be empty."
        )

    if n_results <= 0:

        raise ValueError(
            "n_results must be greater than 0."
        )

    collection = get_collection()

    return collection.query(
        query_texts=[query],
        n_results=n_results,
        include=[
            "documents",
            "distances",
            "metadatas"
        ]
    )


def reset_collection():
    """
    Delete the existing knowledge base and create
    a fresh collection.
    """

    try:

        client.delete_collection(
            name=COLLECTION_NAME
        )

    except ValueError:

        # ChromaDB raises ValueError when the
        # requested collection does not exist.
        pass

    return client.get_or_create_collection(
        name=COLLECTION_NAME
    )