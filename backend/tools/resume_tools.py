from backend.models.resume_model import Resume

def get_user_resume(user_id):
    try:
        db_user_id = int(user_id)
    except (ValueError, TypeError):
        db_user_id = user_id

    resume = Resume.query.filter_by(user_id=db_user_id).first()

    if not resume:
        return "User has not uploaded a resume."

    return resume.text_chunk


