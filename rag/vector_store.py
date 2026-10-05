import os
from pathlib import Path

import chromadb


# local chromadb storage path
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
    # get or create chroma collection

    return client.get_or_create_collection(
        name=COLLECTION_NAME
    )


def add_documents(
    documents: list[str],
    ids: list[str],
    metadatas: list[dict]
):
    # save text chunks + metadata into chromadb

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
    # vector search query against chromadb

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
    # clear and recreate collection

    try:

        client.delete_collection(
            name=COLLECTION_NAME
        )

    except ValueError:

        # ignore if collection doesn't exist yet
        pass

    return client.get_or_create_collection(
        name=COLLECTION_NAME
    )