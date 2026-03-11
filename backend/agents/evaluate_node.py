def evaluate_answer(state, llm):

    question = state.get("question", "")
    answer = state.get("answer", "")
    jd = state.get("job_description", "")

    if not answer:
        state["feedback"] = "No answer provided to evaluate."
        return state

    # Check if the user is trying to change the topic or asking for a specific question type
    topic_check_prompt = f"""
    The candidate was asked: "{question}"
    The candidate replied: "{answer}"
    
    Is the candidate's reply an actual attempt to answer the question, or are they asking to change the topic, skip the question, or ask about something else (e.g., "ask me about python", "let's talk about behavior")?
    
    If it is a request to change topic/skip, reply with "TOPIC_CHANGE: [Brief description of what they want to talk about]".
    If it is an attempt to answer, reply with "PROCEED".
    """
    
    topic_check = llm.invoke(topic_check_prompt).content.strip()
    
    if "TOPIC_CHANGE" in topic_check:
        state["feedback"] = topic_check
        return state

    prompt = f"""
            Role: {state.get('role', 'Software Engineer')}
            Job Description: {jd}
            
            Question asked:
            {question}

            Candidate's Answer:
            {answer}

            Evaluate the candidate's answer based on the role and job description.
            If the answer is completely unrelated to the question, point that out politely.
            Provide constructive feedback. Explain what was correct and what can be improved.
    """

    response = llm.invoke(prompt)

    state["feedback"] = response.content

    return state