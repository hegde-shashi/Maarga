from langchain.tools import tool

@tool
def duckduckgo_search(query: str):
    """
    Search web using DuckDuckGo.
    Use this for real-time information like salaries, company news, and market trends.
    """
    try:
        from langchain_community.tools import DuckDuckGoSearchRun
        search = DuckDuckGoSearchRun()
        return search.run(query)
    except Exception as e:
        if "ddgs" in str(e).lower() or "import" in str(e).lower():
            return "AI Service Error: Web search is temporarily unavailable. Please try again in 1 minute while dependencies are updated."
        return f"Search error: {str(e)}"
