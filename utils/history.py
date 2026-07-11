from langchain_core.messages import HumanMessage, AIMessage

from config import MAX_HISTORY_MESSAGES


def history_to_messages(chat_history: list) -> list:
    """
    Convert chat history into LangChain messages.

    Only the most recent conversation is sent to the rewrite model
    to keep context relevant and avoid confusing it.
    """
    messages = []

    # Keep only the latest history
    recent_history = chat_history[-MAX_HISTORY_MESSAGES:]

    for turn in recent_history:
        role = turn.get("role")
        content = turn.get("content", "")

        if role == "user":
            messages.append(HumanMessage(content=content))

        elif role == "assistant":
            messages.append(AIMessage(content=content))

    return messages


def add_turn(chat_history: list, question: str, answer: str) -> list:
    """
    Store the latest user question and assistant answer.
    """

    updated = chat_history + [
        {
            "role": "user",
            "content": question,
        },
        {
            "role": "assistant",
            "content": answer,
        },
    ]

    # Keep only the latest history
    return updated[-MAX_HISTORY_MESSAGES:]