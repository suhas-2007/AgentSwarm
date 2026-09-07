from rag.vector_store import search_documents


def retrieve_documents(
    query: str,
    n_results: int = 3
) -> list[dict]:
    """
    Retrieve relevant documents from ChromaDB.

    Returns a normalized list of retrieval results
    that can be used by other AgentSwarm components.
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

    if not isinstance(n_results, int):
        raise TypeError(
            "n_results must be an integer."
        )

    if n_results <= 0:
        raise ValueError(
            "n_results must be greater than 0."
        )

    results = search_documents(
        query,
        n_results=n_results
    )

    documents = results.get(
        "documents",
        [[]]
    )[0]

    distances = results.get(
        "distances",
        [[]]
    )[0]

    ids = results.get(
        "ids",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    retrieved = []

    for index, document in enumerate(
        documents
    ):

        metadata = (
            metadatas[index]
            if index < len(metadatas)
            else {}
        )

        retrieved.append(
            {
                "id": (
                    ids[index]
                    if index < len(ids)
                    else None
                ),
                "source": metadata.get(
                    "source"
                ),
                "chunk_id": metadata.get(
                    "chunk_id"
                ),
                "distance": (
                    distances[index]
                    if index < len(distances)
                    else None
                ),
                "content": document
            }
        )

    return retrieved


def format_retrieval_results(
    results: list[dict]
) -> str:
    """
    Convert retrieved documents into a
    readable evidence block for agents.
    """

    if not results:
        return (
            "No relevant documents were "
            "retrieved from the knowledge base."
        )

    sections = []

    for index, result in enumerate(
        results,
        start=1
    ):

        distance = result["distance"]

        if distance is None:
            distance_text = "N/A"
        else:
            distance_text = f"{distance:.4f}"

        sections.append(
            f"""
Document {index}

ID: {result["id"]}
Source: {result["source"]}
Chunk ID: {result["chunk_id"]}
Distance: {distance_text}
Character count: {len(result["content"])}

Content:
{result["content"]}
""".strip()
        )

    return "\n\n".join(
        sections
    )


if __name__ == "__main__":

    query = input(
        "Enter your search query: "
    ).strip()

    try:

        results = retrieve_documents(
            query,
            n_results=3
        )

        print(
            "\n--- RETRIEVED DOCUMENTS ---"
        )

        print(
            f"\nNumber of retrieved documents: "
            f"{len(results)}"
        )

        print(
            format_retrieval_results(
                results
            )
        )

    except Exception as error:

        print(
            f"\nSearch failed: {error}"
        )