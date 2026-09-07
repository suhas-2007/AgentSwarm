from rag.vector_store import search_documents


query = input("Enter your search query: ")


results = search_documents(
    query,
    n_results=3
)


print("\n--- RETRIEVED DOCUMENTS ---")


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


print(
    f"\nNumber of retrieved documents: "
    f"{len(documents)}"
)


for i, document in enumerate(documents):

    print(f"\nDocument {i + 1}")

    print(
        f"ID: {ids[i]}"
    )

    print(
        f"Source: {metadatas[i]['source']}"
    )

    print(
        f"Chunk ID: {metadatas[i]['chunk_id']}"
    )

    print(
        f"Distance: {distances[i]:.4f}"
    )

    print(
        f"Character count: {len(document)}"
    )

    print("Content:")

    print(document)