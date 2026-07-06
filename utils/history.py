from langchain_core.messages import HumanMessage, AIMessage

from config import MAX_HISTORY_MESSAGES


def history_to_messages(chat_history: list) -> list:
    """
    Converts chat_history (list of {"role": ..., "content": ...} dicts)
    into LangChain message objects (HumanMessage / AIMessage) that
    can be passed straight into an LLM call.
    """
    messages = []
    for turn in chat_history:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))
    return messages


def add_turn(chat_history: list, question: str, answer: str) -> list:
    """
    Appends the latest question+answer pair to chat_history,
    then trims it so the history sent to the LLM doesn't grow
    forever (keeps only the most recent MAX_HISTORY_MESSAGES).
    """
    updated = chat_history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ]

    if len(updated) > MAX_HISTORY_MESSAGES:
        updated = updated[-MAX_HISTORY_MESSAGES:]

    return updated