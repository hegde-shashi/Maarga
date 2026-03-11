def generate_question(state, llm):

    role = state.get("role", "Data Scientist")
    jd = state.get("job_description", "")
    feedback = state.get("feedback", "")

    topic_instruction = ""
    if "TOPIC_CHANGE:" in feedback:
        topic = feedback.replace("TOPIC_CHANGE:", "").strip()
        topic_instruction = f"The user wants to change the topic to: {topic}. Please ask a technical question about this new topic."
    else:
        topic_instruction = "Continue the technical interview with a new relevant question based on the job description."

    prompt = f"""
            You are a technical interviewer for the role of {role}.
            Job Description: {jd}
            
            Instruction: {topic_instruction}
            
            Ask one technical interview question that is relevant.
            Only ask the question, do not provide the answer or any explanation.
    """

    response = llm.invoke(prompt)

    state["question"] = response.content

    return state