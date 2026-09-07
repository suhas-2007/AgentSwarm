import chromadb


# Create a local persistent ChromaDB database
client = chromadb.PersistentClient(
    path="./rag/chroma_db"
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
    except Exception:
        pass

    return client.get_or_create_collection(
        name=COLLECTION_NAME
    )