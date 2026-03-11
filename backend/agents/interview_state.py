from typing import TypedDict


class InterviewState(TypedDict):
    role: str
    job_description: str
    question: str
    answer: str
    feedback: str