from langchain.tools import tool

from backend.tools.resume_tools import get_user_resume
from backend.tools.job_tools import get_job_details
from backend.tools.match_tools import resume_job_match
from backend.tools.youtube_tools import youtube_search
from backend.tools.search_tools import duckduckgo_search


@tool
def fetch_resume(user_id: str):
    """Get user's resume content."""
    return get_user_resume(user_id)


@tool
def fetch_job(job_id: str, user_id: str):
    """Get job details."""
    return get_job_details(job_id, user_id)


@tool
def match_resume_job(user_id: str, job_id: str):
    """Compare resume with job."""
    return resume_job_match(user_id, job_id)


@tool
def search_youtube(query: str):
    """
    Search for YouTube videos. 
    MANDATORY: Use this tool whenever the user asks for videos, tutorials, or visual learning resources 
    related to skills, job roles, or interview preparation.
    """
    return youtube_search(query)


TOOLS = [
    fetch_resume,
    fetch_job,
    match_resume_job,
    search_youtube,
    duckduckgo_search
]