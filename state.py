#shared state that every node in your graph can access.

"""
    Shared state passed between all LangGraph nodes.
    Every node reads from this and writes back to it.
    """

from typing import List, TypedDict


class ChatState(TypedDict):
    # Current user question
    question: str
    
    # NEW: standalone version of the question (resolves follow-ups)
    standalone_question:str

    # Router decision
    route: str

    # RAG retrieved chunks
    rag_context: List[str]

    # Web search results
    web_context: List[str]

    # Context passed to the LLM
    retrieved_context: str

    # Final answer
    answer: str

    # Conversation history
    chat_history: List[dict]
