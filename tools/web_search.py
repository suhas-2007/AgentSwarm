import os

from tavily import TavilyClient


tavily = TavilyClient(
    api_key=os.getenv(
        "TAVILY_API_KEY"
    )
)


MAX_QUERY_LENGTH = 1500


def web_search(
    query: str
) -> str:

    query = " ".join(
        query.split()
    ).strip()

    if not query:

        raise ValueError(
            "Web search query cannot be empty."
        )

    if len(query) > MAX_QUERY_LENGTH:

        query = query[
            :MAX_QUERY_LENGTH
        ]

    results = tavily.search(
        query=query,
        max_results=5
    )

    formatted_results = []

    for result in results["results"]:

        formatted_results.append(
            f"Title: {result['title']}\n"
            f"URL: {result['url']}\n"
            f"Content: {result['content']}\n"
        )

    return "\n".join(
        formatted_results
    )