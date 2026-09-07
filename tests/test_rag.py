from pathlib import Path

from rag.chunker import chunk_text
from rag.vector_store import (
    add_documents,
    reset_collection,
    search_documents
)


def test_chunking_creates_chunks():

    text = (
        "FastAPI is a Python web framework. "
        "It supports request validation. "
        "Pydantic is used for data validation."
    )

    chunks = chunk_text(
        text,
        chunk_size=100,
        overlap=20
    )

    assert len(chunks) > 0

    for chunk in chunks:
        assert isinstance(chunk, str)
        assert len(chunk) > 0


def test_documents_can_be_added_and_retrieved():

    reset_collection()

    documents = [
        "FastAPI is a Python web framework.",
        "Pydantic provides data validation.",
        "ChromaDB is a vector database."
    ]

    ids = [
        "test_doc_1",
        "test_doc_2",
        "test_doc_3"
    ]

    metadatas = [
        {
            "source": "fastapi.txt",
            "chunk_id": 0
        },
        {
            "source": "pydantic.txt",
            "chunk_id": 0
        },
        {
            "source": "chromadb.txt",
            "chunk_id": 0
        }
    ]

    add_documents(
        documents,
        ids,
        metadatas
    )

    results = search_documents(
        "Python web framework",
        n_results=3
    )

    retrieved_documents = results.get(
        "documents",
        [[]]
    )[0]

    assert len(retrieved_documents) > 0

    assert any(
        "FastAPI" in document
        for document in retrieved_documents
    )


def test_metadata_is_preserved():

    reset_collection()

    documents = [
        "FastAPI supports request validation."
    ]

    ids = [
        "metadata_test_1"
    ]

    metadatas = [
        {
            "source": "fastapi.txt",
            "chunk_id": 5
        }
    ]

    add_documents(
        documents,
        ids,
        metadatas
    )

    results = search_documents(
        "request validation",
        n_results=1
    )

    retrieved_ids = results.get(
        "ids",
        [[]]
    )[0]

    retrieved_metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    assert retrieved_ids[0] == "metadata_test_1"

    assert retrieved_metadatas[0]["source"] == (
        "fastapi.txt"
    )

    assert retrieved_metadatas[0]["chunk_id"] == 5


def test_reset_collection_removes_previous_documents():

    reset_collection()

    documents = [
        "This is a temporary test document."
    ]

    ids = [
        "reset_test_1"
    ]

    metadatas = [
        {
            "source": "temporary.txt",
            "chunk_id": 0
        }
    ]

    add_documents(
        documents,
        ids,
        metadatas
    )

    reset_collection()

    results = search_documents(
        "temporary test document",
        n_results=1
    )

    retrieved_documents = results.get(
        "documents",
        [[]]
    )[0]

    assert len(retrieved_documents) == 0