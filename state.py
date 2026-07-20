from typing import TypedDict, List, Dict, Any


class ChatState(TypedDict):
    # -------------------------
    # User Question
    # -------------------------
    question: str
    standalone_question: str

    # -------------------------
    # Router
    # -------------------------
    route: str

    # -------------------------
    # Context
    # -------------------------
    rag_context: List[str]
    web_context: List[str]
    retrieved_context: str

    # -------------------------
    # Final Answer
    # -------------------------
    answer: str

    # -------------------------
    # Conversation History
    # -------------------------
    chat_history: List[dict]

    # -------------------------
    # Image Search
    # -------------------------
    fetched_images: List[Dict[str, Any]]

    # Last searched subject
    last_image_subject: str

    # -------------------------
    # Image Generation (NEW)
    # -------------------------
    generated_images: List[str]

    # -------------------------
    # Conversation Memory
    # -------------------------
    current_topic: str
    last_route: str

    # -------------------------
    # Vision
    # -------------------------
    uploaded_image: str
    image_description: str
    is_new_image_upload: bool