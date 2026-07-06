from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage

from config import GROQ_API_KEY, LLM_MODEL
from state import ChatState
from prompts.answer_prompt import ANSWER_PROMPT
from utils.history import add_turn


llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=LLM_MODEL,
    temperature=0.3,
)


def answer_node(state: ChatState) -> ChatState:
    """
    Final node in the graph. Polishes the draft answer from
    llm/rag/web, then saves this turn into chat_history so the
    next question has memory of it.
    """
    question = state["question"]
    draft_answer = state["answer"]

    # Polish formatting/clarity without changing facts
    prompt = ANSWER_PROMPT.format(draft_answer=draft_answer)
    response = llm.invoke([SystemMessage(content=prompt)])
    final_answer = response.content

    # Save this turn into memory (defined in utils/history.py)
    chat_history = state.get("chat_history", [])
    state["chat_history"] = add_turn(chat_history, question, final_answer)

    state["answer"] = final_answer
    return state