from langchain_community.tools import DuckDuckGoSearchRun
from langchain.tools import tool

@tool
def duckduckgo_search(query: str):
    """
    Search web using DuckDuckGo.
    Use this for real-time information like salaries, company news, and market trends.
    """
    search = DuckDuckGoSearchRun()
    return search.run(query)
