from typing import TypedDict, List, Dict, Any
class ChatState(TypedDict):
    # User question
    question: str
    standalone_question: str

    # Router
    route: str

    # Context
    rag_context: List[str]
    web_context: List[str]
    retrieved_context: str

    # Final answer
    answer: str

    # Conversation history
    chat_history: List[dict]

    # Image search
    fetched_images: List[Dict[str, Any]]

    # Last searched person/object for image search
    last_image_subject: str

    # NEW  Current conversation topic
    current_topic: str

    # NEW  Previous route
    last_route: str

    # Vision
    uploaded_image: str
    image_description: str
    is_new_image_upload: bool