from typing import TypedDict, List, Dict, Any


class ChatState(TypedDict):
    # Original user question
    question: str

    # Rewritten standalone question
    standalone_question: str

    # Router decision
    route: str

    # RAG retrieved chunks
    rag_context: List[str]

    # Web search results
    web_context: List[str]

    # Combined context passed to the LLM
    retrieved_context: str

    # Final response
    answer: str

    # Conversation memory
    chat_history: List[dict]

    # Image search results
    fetched_images: List[Dict[str, Any]]

    # NEW: remembers the last image subject
    # Example: "Virat Kohli", "Rohit Sharma"
    last_image_subject: str