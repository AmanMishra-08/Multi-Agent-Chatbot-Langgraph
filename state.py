#shared state that every node in your graph can access.
from typing import List, TypedDict


class ChatState(TypedDict):
    """
    Shared state passed between all LangGraph nodes.
    Every node reads from this and writes back to it.
    """

    # User's current question
    question: str

    # Router's decision: "llm", "rag", or "web"
    route: str

    # Retrieved chunks (RAG) or search results (web) for this turn
    documents: List[str]

    # Final answer for this turn
    answer: str

    # Full conversation memory: list of {"role": ..., "content": ...}
    chat_history: List[dict]