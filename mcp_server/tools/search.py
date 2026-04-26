"""Web search tool using DuckDuckGo (no API key required)."""

from duckduckgo_search import DDGS


async def web_search(query: str, max_results: int = 5) -> str:
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(
                f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n"
            )
    if not results:
        return "No results found."
    return "\n---\n".join(results)
