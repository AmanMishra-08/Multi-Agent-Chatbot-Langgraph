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


def router_node(state: ChatState) -> ChatState:
    question = state["question"]

    messages = [
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=question),
    ]

    response = llm.invoke(messages)
    decision = response.content.strip().lower()

    # Safety net: fall back to "llm" if the model returns
    # something unexpected instead of one of our three routes.
    if decision not in ("rag", "web", "llm"):
        decision = "llm"

    state["route"] = decision
    return state