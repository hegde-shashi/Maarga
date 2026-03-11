from backend.models.job_model import Jobs
from backend.services.job_services import build_job_context


def get_job_details(job_id, user_id):
    try:
        db_job_id = int(job_id)
        db_user_id = int(user_id)
    except (ValueError, TypeError):
        db_job_id = job_id
        db_user_id = user_id

    job = Jobs.query.filter_by(
        id=db_job_id,
        user_id=db_user_id
    ).first()

    if not job:
        return "Job not found."

    return {
        "company": job.company,
        "role": job.job_title,
        "progress": job.progress,
        "description": build_job_context(job)
    }