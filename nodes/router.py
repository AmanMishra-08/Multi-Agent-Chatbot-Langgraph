import re

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from config import GROQ_API_KEY, LLM_MODEL
from state import ChatState
from prompts.router_prompt import ROUTER_PROMPT
from utils.history import history_to_messages


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


def router_node(state: ChatState) -> ChatState:

    question = state["standalone_question"].strip()
    lower_question = question.lower()

    # -------------------------
    # Rule 1: Image Search
    # -------------------------
    if any(re.search(rf"\b{re.escape(word)}\b", lower_question) for word in IMAGE_WORDS):
        state["route"] = "image_search"
        print("[router] Rule -> image_search")
        return state

    # -------------------------
    # Rule 2: Web Search
    # -------------------------
    if any(re.search(rf"\b{re.escape(word)}\b", lower_question) for word in WEB_WORDS):
        state["route"] = "web"
        print("[router] Rule -> web")
        return state

    # -------------------------
    # Otherwise ask the LLM
    # -------------------------
    # LLM fallback — classify based on the standalone question ALONE.
    # rewrite_query_node already resolved any needed context into
    # standalone_question, so passing raw chat_history here just adds
    # noise that can make classification inconsistent run to run.
    messages = [
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=question),
    ]

    response = llm.invoke(messages)


    raw = response.content.strip().lower()

    print(f"[router_node] raw = {raw}")

    if "rag" in raw:
        route = "rag"

    elif "web" in raw:
        route = "web"

    elif "image_search" in raw:
        route = "image_search"

    else:
        route = "llm"

    print(f"[router_node] final = {route}")

    state["route"] = route

    return state