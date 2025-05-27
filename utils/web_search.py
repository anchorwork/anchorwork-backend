import os, requests, json, logging
from dotenv import load_dotenv
load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
ENGINE      = "google"

def web_search(query: str, num_results: int = 3) -> str:
    """
    Perform a web search using the SerpAPI.

    Parameters:
    - query (str): The search query string.
    - num_results (int): The number of search results to return (max 10).

    Returns:
    - str: Formatted search results or an error message.
    """
    if not SERPAPI_KEY:
        logging.error("Missing SERPAPI_KEY environment variable.")
        return "❌ Web search not available: missing SERPAPI_KEY"

    num_results = min(num_results, 10)

    params = {
        "q":       query,
        "api_key": SERPAPI_KEY,
        "engine":  ENGINE,
        "num":     num_results
    }
    headers = {
        "User-Agent": "web_search_agent/1.0"
    }
    try:
        # *** correct endpoint ***
        resp = requests.get("https://serpapi.com/search.json", params=params, headers=headers, timeout=20)
        if resp.status_code != 200:
            return f"❌ SerpAPI HTTP {resp.status_code}: {resp.text[:120]}"

        data = resp.json()
        results = []
        for res in data.get("organic_results", [])[:num_results]:
            title   = res.get("title", "")
            link    = res.get("link", "")
            snippet = res.get("snippet", "")
            results.append(f"- [{title}]({link}) — {snippet}")

        return "\n\n".join(results) if results else "❌ No search results."
    except Exception as e:
        logging.exception("Exception during web search")
        return f"❌ Web Search Error: {e}"
