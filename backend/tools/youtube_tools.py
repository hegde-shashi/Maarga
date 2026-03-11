import requests


def youtube_search(query):
    """Returns a YouTube search URL for the given query."""
    clean_query = query.replace(" ", "+")
    url = f"https://www.youtube.com/results?search_query={clean_query}"
    
    return f"I have found some relevant YouTube videos for you. You can view the results here: {url}"