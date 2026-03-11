from langgraph.graph import StateGraph
from langgraph.graph import END

from backend.agents.interview_state import InterviewState
from backend.agents.question_node import generate_question
from backend.agents.evaluate_node import evaluate_answer


def build_interview_graph(llm):

    graph = StateGraph(InterviewState)

    graph.add_node("question", lambda s: generate_question(s, llm))
    graph.add_node("evaluate", lambda s: evaluate_answer(s, llm))

    # Conditional logic: If there's an answer to evaluate, start with evaluation.
    # Otherwise, start directly with a question.
    def decide_entry_node(state):
        if state.get("answer") and state.get("question"):
            return "evaluate"
        return "question"

    graph.set_conditional_entry_point(
        decide_entry_node,
        {
            "evaluate": "evaluate",
            "question": "question"
        }
    )

    graph.add_edge("evaluate", "question")
    graph.add_edge("question", END)

    return graph.compile()