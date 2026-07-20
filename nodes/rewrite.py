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
3. If the user specifies an action, descriptive detail, or a count without an explicit action verb (e.g., "3 images", "in a suit", "young boy and girl") and the history shows they were just creating or drawing images, prepend the implied command (e.g., "draw a young boy and girl").
4. Never invent a new subject unrelated to the chat history.
5. Never answer the question.
6. Return ONLY the rewritten question.

Examples:
- History: User asks about Rohit Sharma -> User follow-up: "3 image" -> Rewrite: "3 images of rohit sharma"
- History: User asks to draw a lion -> User follow-up: "in a suit" -> Rewrite: "draw a lion in a suit"
- History: User says draw a man with girl -> User follow-up: "young boy and girl" -> Rewrite: "draw a young boy and girl"
"""

def rewrite_query_node(state: ChatState) -> ChatState:
    question = state["question"].strip()
    chat_history = state.get("chat_history", [])
    last_subject = state.get("last_image_subject", "")
    last_route = state.get("last_route", "")

    print("=" * 50)
    print("QUESTION:", question)
    print("LAST SUBJECT:", repr(last_subject))
    print("LAST ROUTE:", repr(last_route))
    print("=" * 50)

    has_uploaded_image = bool(state.get("uploaded_image"))
    lower = question.lower().strip()

    # --------------------------------------------------
    # New Shortcut: Casual Chat / Thanks Filter
    # --------------------------------------------------
    casual_phrases = ["thank you", "thanks", "ok thanks", "ok thank you", "okay thanks", "cool", "awesome", "bye"]
    if lower in casual_phrases or lower == "ok" or lower == "okay":
        print("[rewrite] Casual phrase detected. Bypassing LLM rewrite.")
        state["standalone_question"] = question
        return state

    # --------------------------------------------------
    # Shortcut 1: No history
    # --------------------------------------------------
    if not chat_history and not has_uploaded_image:
        state["standalone_question"] = question
        return state

    # --------------------------------------------------
    # Shortcut 2: Image search follow-up (Guaranteed Regex Match)
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
    # Shortcut 3: Uploaded image follow-up
    # --------------------------------------------------
    if has_uploaded_image:
        pronouns = ["it", "this", "that", "its"]
        words = lower.split()

        is_fresh_image_query = any(w in lower for w in ["what", "explain", "describe", "show"]) and any(p in words for p in ["this", "image", "pic", "photo"])

        if is_fresh_image_query or any(p in words for p in pronouns):
            rewritten = re.sub(r"\bits\b", "the uploaded image's", question, flags=re.IGNORECASE)
            rewritten = re.sub(r"\bit\b", "the uploaded image", rewritten, flags=re.IGNORECASE)
            rewritten = re.sub(r"\bthis\b", "the uploaded image", rewritten, flags=re.IGNORECASE)
            rewritten = re.sub(r"\bthat\b", "the uploaded image", rewritten, flags=re.IGNORECASE)

            state["web_context"] = []
            state["rag_context"] = []
            state["retrieved_context"] = ""
            
            print("[rewrite] uploaded-image shortcut ->", rewritten)
            state["standalone_question"] = rewritten
            return state

    # --------------------------------------------------
    # Shortcut 4: Direct standalone informational queries
    # --------------------------------------------------
    if lower.startswith(("what is", "who is", "where is", "how does", "why does")):
        if not any(p in lower.split() for p in ["it", "this", "that"]):
            print("[rewrite] Direct inquiry shortcut triggered ->", question)
            state["standalone_question"] = question
            return state

    # --------------------------------------------------
    # Shortcut 5: Image Generation Requests
    # --------------------------------------------------
    image_gen_words = ["generate", "create", "draw", "paint", "illustrate", "design", "render"]

    if any(re.search(rf"\b{re.escape(word)}\b", lower) for word in image_gen_words):
        print("[rewrite] Image generation shortcut ->", question)
        state["standalone_question"] = question
        return state

    # --------------------------------------------------
    # LLM Rewrite Fallback
    # --------------------------------------------------
    recent_history = chat_history[-4:]
    system_content = REWRITE_PROMPT
    
    if last_subject:
        system_content += f"\nNote: The last discussed image subject was '{last_subject}'."
    
    # 🌟 AIRTIGHT FIX: Explicitly command the LLM to prepend the action word
    if last_route == "image_gen":
        system_content += (
            "\nCRITICAL: The user is currently in an image generation flow. "
            "If their new question is just a descriptive phrase (e.g., 'old boy and girl') without action verbs, "
            "they want to generate a new image matching this description. "
            "Prepend an action verb like 'Draw' or 'Generate image of' to their query."
        )

    if has_uploaded_image:
        system_content += "\nNote: There is an active uploaded image/document in the chat session. Resolve queries with respect to this uploaded asset."
    messages = [SystemMessage(content=system_content)]
    messages.extend(history_to_messages(recent_history))
    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)
    rewritten = response.content.strip().strip('"')

    print(f"[rewrite] LLM: {question!r} -> {rewritten!r}")
    state["standalone_question"] = rewritten
    return state