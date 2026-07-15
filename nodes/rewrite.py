import re

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

REWRITE_PROMPT = """
You rewrite short conversational follow-up questions into standalone descriptive queries.

Rules:
1. If the question is already complete, return it EXACTLY unchanged.
2. Resolve pronouns (it, this, that, he, she, him, her) using the conversation history.
3. If the user specifies an action or a count without a subject (e.g., "3 images", "show more", "another one"), append the last discussed subject from the history.
4. Never invent a new subject.
5. Never answer the question.
6. Return ONLY the rewritten question.

Examples:
- History: User asks about Rohit Sharma -> User follow-up: "3 image" -> Rewrite: "3 images of rohit sharma"
- History: User asks about Lion -> User follow-up: "in a suit" -> Rewrite: "lion in a suit"
"""

def rewrite_query_node(state: ChatState) -> ChatState:
    question = state["question"].strip()
    chat_history = state.get("chat_history", [])
    last_subject = state.get("last_image_subject", "")

    print("=" * 50)
    print("QUESTION:", question)
    print("LAST SUBJECT:", repr(last_subject))
    print("=" * 50)

    has_uploaded_image = bool(state.get("uploaded_image"))
    lower = question.lower().strip()

    # --------------------------------------------------
    # Shortcut 1: No history
    # --------------------------------------------------
    if not chat_history and not has_uploaded_image:
        state["standalone_question"] = question
        return state

    # --------------------------------------------------
    # Shortcut 2: Image follow-up (Guaranteed Regex Match)
    # --------------------------------------------------
    if last_subject:
        has_number = re.search(r"\d+", lower)
        has_image_keyword = any(w in lower for w in ["image", "photo", "pic", "picture"])
        has_nav_keyword = any(w in lower for w in ["more", "another", "next"])

        if (has_number and has_image_keyword) or has_nav_keyword or (lower in ["image", "photos", "pics"]):
            if has_number:
                rewritten = f"{has_number.group()} photos of {last_subject}"
            elif "more" in lower:
                rewritten = f"more photos of {last_subject}"
            else:
                rewritten = f"photo of {last_subject}"

            print("[rewrite] image shortcut triggered ->", rewritten)
            state["standalone_question"] = rewritten
            return state

    # --------------------------------------------------
    # Shortcut 3: Uploaded image follow-up (🌟 FIX: Safe Whole-Word Token Swap)
    # --------------------------------------------------
    # --------------------------------------------------
    # Shortcut 3: Uploaded image follow-up (🌟 FIX: Safe Token Swap + Context Flush)
    # --------------------------------------------------
    if has_uploaded_image:
        pronouns = ["it", "this", "that", "its"]
        words = lower.split()

        # Check if the user is asking a basic question about the new image
        # (e.g., "what is this?", "explain it")
        is_fresh_image_query = any(w in lower for w in ["what", "explain", "describe", "show"]) and any(p in words for p in ["this", "image", "pic", "photo"])

        if is_fresh_image_query or any(p in words for p in pronouns):
            # 1. Clean up pronouns using safe regular expressions
            rewritten = re.sub(r"\bits\b", "the uploaded image's", question, flags=re.IGNORECASE)
            rewritten = re.sub(r"\bit\b", "the uploaded image", rewritten, flags=re.IGNORECASE)
            rewritten = re.sub(r"\bthis\b", "the uploaded image", rewritten, flags=re.IGNORECASE)
            rewritten = re.sub(r"\bthat\b", "the uploaded image", rewritten, flags=re.IGNORECASE)

            # 2. 🌟 THE FIX: If it's a new image request, clear out legacy text states
            # so the Vision Node doesn't inherit "Cyfuture" or web search histories.
            state["web_context"] = []
            state["rag_context"] = []
            state["retrieved_context"] = ""
            
            print("[rewrite] uploaded-image shortcut ->", rewritten)
            state["standalone_question"] = rewritten
            return state

    # --------------------------------------------------
    # Shortcut 4: Already standalone (4+ words, no pronouns)
    # --------------------------------------------------
    if len(question.split()) >= 4:
        if not any(p in lower.split() for p in ["it", "this", "that", "they", "he", "she", "him", "her"]):
            state["standalone_question"] = question
            return state

    # --------------------------------------------------
    # LLM Rewrite Fallback
    # --------------------------------------------------
    recent_history = chat_history[-4:]
    system_content = REWRITE_PROMPT
    if last_subject:
        system_content += f"\nNote: The last discussed image subject was '{last_subject}'."

    messages = [SystemMessage(content=system_content)]
    messages.extend(history_to_messages(recent_history))
    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)
    rewritten = response.content.strip().strip('"')

    print(f"[rewrite] LLM: {question!r} -> {rewritten!r}")
    state["standalone_question"] = rewritten
    return state