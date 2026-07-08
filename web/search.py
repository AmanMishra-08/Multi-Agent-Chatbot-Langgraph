from tavily import TavilyClient

from config import TAVILY_API_KEY


_client = TavilyClient(api_key=TAVILY_API_KEY)


def search(query: str, max_results: int = 5) -> list[str]:
    """
    Runs a Tavily web search and returns a list of plain text
    strings, each combining a result's title and content.
    """
    query = query[:400]

    response = _client.search(
        query=query,
        max_results=max_results,
        topic="news",   # biases results toward news, not general/old web pages
        days=30,        # limits results to the last 30 days
    )

    results = [
        f"{r['title']}: {r['content']}"
        for r in response.get("results", [])
    ]
    return results