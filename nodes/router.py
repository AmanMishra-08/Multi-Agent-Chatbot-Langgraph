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


def router_node(state: ChatState) -> ChatState:
    question = state["standalone_question"]
    chat_history = state.get("chat_history", [])

    messages = [SystemMessage(content=ROUTER_PROMPT)]

    messages.extend(history_to_messages(chat_history))

    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)

    raw_decision = response.content.strip().lower()
    print(f"[router_node] raw LLM output: {raw_decision!r}")  # TEMP DEBUG

    # Robust matching instead of strict equality — handles cases where
    # the model adds punctuation or extra words despite instructions
    # to return only one word.
    if "rag" in raw_decision:
        decision = "rag"
    elif "web" in raw_decision:
        decision = "web"
    else:
        decision = "llm"

    print(f"[router_node] final route: {decision}")  # TEMP DEBUG

    state["route"] = decision

    return state