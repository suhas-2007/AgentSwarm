from pathlib import Path

from rag.vector_store import (
    add_documents,
    reset_collection
)

from rag.chunker import chunk_text


DOCUMENTS_DIR = Path("rag/documents")


def load_documents():
    documents = []
    ids = []
    metadatas = []

    for file_path in DOCUMENTS_DIR.glob("*.txt"):

        text = file_path.read_text(
            encoding="utf-8"
        )

        chunks = chunk_text(
            text,
            chunk_size=500,
            overlap=100
        )

        for index, chunk in enumerate(chunks):

            documents.append(chunk)

            ids.append(
                f"{file_path.stem}_chunk_{index}"
            )

            metadatas.append(
                {
                    "source": file_path.name,
                    "chunk_id": index
                }
            )

    return documents, ids, metadatas


if __name__ == "__main__":

    documents, ids, metadatas = load_documents()

    if not documents:
        print("No documents found.")

    else:

        # Remove previous knowledge base
        reset_collection()

        # Add new chunks with metadata
        add_documents(
            documents,
            ids,
            metadatas
        )

        print(
            f"Added {len(documents)} chunk(s) "
            "to ChromaDB."
        )