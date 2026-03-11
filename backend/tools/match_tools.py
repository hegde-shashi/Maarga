from backend.tools.resume_tools import get_user_resume
from backend.tools.job_tools import get_job_details


def resume_job_match(user_id, job_id):

    resume = get_user_resume(user_id)
    job = get_job_details(job_id, user_id)

    return {
        "resume": resume,
        "job_description": job["description"],
        "role": job["role"],
        "company": job["company"]
    }