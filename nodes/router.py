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

# Deterministic RAG keywords -- these should always hit the knowledge
# base regardless of what the LLM fallback might guess on a given run.
# Covers common misspellings of "cyfuture" too, since typos were
# slipping through inconsistently before.
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
    lower_question = question.lower()
    has_image = bool(state.get("uploaded_image"))

    # -------------------------
    # Rule 0: Vision -- ONLY force vision for a brand-new upload this
    # turn. This guarantees a fresh image always gets analyzed at
    # least once, regardless of what the user typed alongside it.
    # -------------------------
    if state.get("is_new_image_upload"):
        state["route"] = "vision"
        print("[router] Rule -> vision (new image uploaded)")
        return state

    # If an image is attached (but not new this turn), SKIP the
    # keyword rules below entirely and go straight to the vision-aware
    # LLM classification. Keyword matching can't reliably tell "search
    # the web for an image" apart from "analyze my uploaded image" --
    # both can contain words like "image"/"photo" -- so once an image
    # is in play, real judgment is needed instead of a keyword guess.
    if not has_image:

        # -------------------------
        # Rule 1: RAG (deterministic -- company/knowledge base topics)
        # -------------------------
        if any(word in lower_question for word in RAG_WORDS):
            state["route"] = "rag"
            print("[router] Rule -> rag")
            return state

        # -------------------------
        # Rule 2: Image Search (web image search, e.g. "photo of X")
        # -------------------------
        if any(re.search(rf"\b{re.escape(word)}\b", lower_question) for word in IMAGE_WORDS):
            state["route"] = "image_search"
            print("[router] Rule -> image_search")
            return state

        # -------------------------
        # Rule 3: Web Search
        # -------------------------
        if any(re.search(rf"\b{re.escape(word)}\b", lower_question) for word in WEB_WORDS):
            state["route"] = "web"
            print("[router] Rule -> web")
            return state

    # -------------------------
    # LLM fallback -- always used when an image is attached, or when
    # no keyword rule matched. Tells the model whether an image is
    # currently attached, and lets it genuinely judge whether THIS
    # question is still about that image (-> vision) or not.
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
    else:
        route = "llm"

    print(f"[router_node] final = {route}")
    print("Final Route:", route)
    state["route"] = route
    return state