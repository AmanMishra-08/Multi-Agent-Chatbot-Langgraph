import re

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from config import GROQ_API_KEY, LLM_MODEL
from state import ChatState
from prompts.router_prompt import ROUTER_PROMPT


llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=LLM_MODEL,
    temperature=0,
)


IMAGE_WORDS = [
    "image",
    "images",
    "photo",
    "photos",
    "picture",
    "pictures",
    "pic",
    "wallpaper",
]

IMAGE_GEN_WORDS = [
    "generate",
    "create",
    "draw",
    "make",
    "design",
    "paint",
    "illustrate",
    "render",
]

# NEW FIX: Catch phrases common in generation rewrites so they don't trip image_search
IMAGE_GEN_PHRASES = [
    "image of",
    "images of",
    "picture of",
    "pictures of",
    "photo of",
    "photos of",
    "pic of",
]

WEB_WORDS = [
    "latest",
    "today",
    "current",
    "news",
    "live",
    "weather",
    "score",
    "stock",
    "price",
    "incident",
    "breaking",
]

RAG_WORDS = [
    "cyfuture",
    "cufuture",
    "cyfutur",
    "leave policy",
    "hr policy",
    "refund policy",
    "privacy policy",
    "security policy",
    "shipping policy",
    "payment policy",
    "data protection policy",
]


def router_node(state: ChatState) -> ChatState:

    question = state["standalone_question"].strip()
    print("\nROUTER QUESTION:", question)
    lower_question = question.lower().strip()
    has_image = bool(state.get("uploaded_image"))

    # --------------------------------------------------
    # 🌟 Rule -1: Casual Pleasantry / Thanks Filter
    # --------------------------------------------------
    casual_phrases = ["thank you", "thanks", "ok thanks", "ok thank you", "okay thanks", "cool", "awesome", "bye", "ok", "okay"]
    if lower_question in casual_phrases:
        state["route"] = "llm"
        state["last_route"] = "llm"  # 🌟 Added last_route tracking
        print("[router] Rule -> llm (Casual pleasantry bypassed search/RAG)")
        return state

    # -------------------------
    # Rule 0: Vision -- ONLY force vision for a brand-new upload this
    # turn. This guarantees a fresh image always gets analyzed at
    # least once, regardless of what the user typed alongside it.
    # -------------------------
    if state.get("is_new_image_upload"):
        state["route"] = "vision"
        state["last_route"] = "vision"  # 🌟 Added last_route tracking
        print("[router] Rule -> vision (new image uploaded)")
        return state

    # If an image is attached (but not new this turn), SKIP the
    # keyword rules below entirely and go straight to the vision-aware
    # LLM classification.
    if not has_image:

        # -------------------------
        # Rule 0: RAG (deterministic -- company/knowledge base topics)
        # -------------------------
        if any(word in lower_question for word in RAG_WORDS):
            state["route"] = "rag"
            state["last_route"] = "rag"  # 🌟 Added last_route tracking
            print("[router] Rule -> rag")
            return state
                
        # -------------------------
        # Rule 1: Image Generation (Prioritized)
        # -------------------------
        # Check standard verbs ("draw", "create") OR rewritten phrases ("image of a...")
        has_gen_word = any(re.search(rf"\b{re.escape(word)}\b", lower_question) for word in IMAGE_GEN_WORDS)
        has_gen_phrase = any(phrase in lower_question for phrase in IMAGE_GEN_PHRASES)

        if has_gen_word or has_gen_phrase:
            state["route"] = "image_gen"
            state["last_route"] = "image_gen"  # 🌟 Added last_route tracking
            print("[router] Rule -> image_gen")
            return state

        # -------------------------
        # Rule 2: Image Search (web image search, e.g. "photo of X")
        # -------------------------
        if any(re.search(rf"\b{re.escape(word)}\b", lower_question) for word in IMAGE_WORDS):
            state["route"] = "image_search"
            state["last_route"] = "image_search"  # 🌟 Added last_route tracking
            print("[router] Rule -> image_search")
            return state

        # -------------------------
        # Rule 3: Web Search
        # -------------------------
        if any(re.search(rf"\b{re.escape(word)}\b", lower_question) for word in WEB_WORDS):
            state["route"] = "web"
            state["last_route"] = "web"  # 🌟 Added last_route tracking
            print("[router] Rule -> web")
            return state

    # -------------------------
    # LLM fallback
    # -------------------------
    messages = [
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(
            content=f"""Image currently attached: {"Yes" if has_image else "No"}

Question:
{question}

Remember: prefer "web" over "llm" for specific facts about named events,
missions, or people that could be outdated or uncertain."""
        ),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip().lower()
    print("LLM Router Output:", raw)
    print(f"[router_node] raw = {raw}")

    if "rag" in raw:
        route = "rag"
    elif "vision" in raw:
        route = "vision"
    elif "web" in raw:
        route = "web"
    elif "image_search" in raw:
        route = "image_search"
    elif "image_gen" in raw:
        route = "image_gen"    
    else:
        route = "llm"

    print(f"[router_node] final = {route}")
    print("Final Route:", route)
    
    # 🌟 Added sync for both variables down here
    state["route"] = route
    state["last_route"] = route
    
    return state