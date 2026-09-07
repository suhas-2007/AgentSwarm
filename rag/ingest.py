from pathlib import Path

from rag.vector_store import (
    add_documents,
    reset_collection
)

from rag.chunker import chunk_text


# Resolve the documents directory relative to
# this file so ingestion works regardless of
# the current working directory.
DOCUMENTS_DIR = (
    Path(__file__).resolve().parent
    / "documents"
)


def load_documents():
    documents = []
    ids = []
    metadatas = []

    if not DOCUMENTS_DIR.exists():

        raise FileNotFoundError(
            f"Documents directory not found: "
            f"{DOCUMENTS_DIR}"
        )

    for file_path in sorted(
        DOCUMENTS_DIR.glob("*.txt")
    ):

        try:

            text = file_path.read_text(
                encoding="utf-8"
            )

        except OSError as exc:

            raise RuntimeError(
                f"Could not read document "
                f"'{file_path.name}'."
            ) from exc

        chunks = chunk_text(
            text,
            chunk_size=500,
            overlap=100
        )

        for index, chunk in enumerate(
            chunks
        ):

            documents.append(
                chunk
            )

            ids.append(
                f"{file_path.stem}_chunk_{index}"
            )

            metadatas.append(
                {
                    "source": file_path.name,
                    "chunk_id": index
                }
            )

    return (
        documents,
        ids,
        metadatas
    )


if __name__ == "__main__":

    documents, ids, metadatas = (
        load_documents()
    )

    if not documents:

        print(
            "No documents found."
        )

    else:

        # Remove the previous knowledge base
        # before rebuilding it from the current
        # document set.
        reset_collection()

        # Add new chunks with metadata.
        add_documents(
            documents,
            ids,
            metadatas
        )

        print(
            f"Added {len(documents)} chunk(s) "
            "to ChromaDB."
        )