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
        isinstance(documents, list)
        and isinstance(ids, list)
        and isinstance(metadatas, list)
    ):

        raise TypeError(
            "documents, ids, and metadatas "
            "must be lists."
        )

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

    for document in documents:

        if not isinstance(
            document,
            str
        ) or not document.strip():

            raise ValueError(
                "documents must contain "
                "non-empty strings."
            )

    for document_id in ids:

        if not isinstance(
            document_id,
            str
        ) or not document_id.strip():

            raise ValueError(
                "ids must contain "
                "non-empty strings."
            )

    for metadata in metadatas:

        if not isinstance(
            metadata,
            dict
        ):

            raise TypeError(
                "metadatas must contain "
                "dictionaries."
            )

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

    If the knowledge base is empty, return an empty
    result structure instead of failing.
    """

    if not isinstance(
        query,
        str
    ):

        raise TypeError(
            "query must be a string."
        )

    query = query.strip()

    if not query:

        raise ValueError(
            "query cannot be empty."
        )

    if not isinstance(
        n_results,
        int
    ):

        raise TypeError(
            "n_results must be an integer."
        )

    if n_results <= 0:

        raise ValueError(
            "n_results must be greater than 0."
        )

    collection = get_collection()

    document_count = collection.count()

    if document_count == 0:

        return {
            "documents": [[]],
            "distances": [[]],
            "ids": [[]],
            "metadatas": [[]]
        }

    n_results = min(
        n_results,
        document_count
    )

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