from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from config import GROQ_API_KEY, LLM_MODEL
from state import ChatState
from utils.history import history_to_messages


llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=LLM_MODEL,
    temperature=0,
)


REWRITE_PROMPT = """Given the conversation history and the latest user question, rewrite the latest question into a short, standalone question (under 20 words) that makes sense without needing the history. Resolve pronouns like "they", "it", "that", "this" using the history. If the question is already standalone, return it unchanged. Return ONLY the rewritten question — no explanation, no preamble, no quotes."""

def rewrite_query_node(state: ChatState) -> ChatState:
    question = state["question"]
    chat_history = state.get("chat_history", [])

    if not chat_history:
        state["standalone_question"] = question
        return state

    messages = [SystemMessage(content=REWRITE_PROMPT)]
    messages.extend(history_to_messages(chat_history))
    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)
    rewritten = response.content.strip().strip('"')

    print(f"[rewrite_query_node] original: {question!r} -> standalone: {rewritten!r}")  # TEMP DEBUG

    state["standalone_question"] = rewritten
    return state