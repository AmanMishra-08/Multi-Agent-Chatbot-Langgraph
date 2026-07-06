from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from config import GROQ_API_KEY, LLM_MODEL
from state import ChatState
from utils.history import history_to_messages


llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=LLM_MODEL,
    temperature=0.7,
)


def llm_node(state: ChatState) -> ChatState:
    question = state["question"]
    chat_history = state.get("chat_history", [])

    # Convert stored history into LangChain message objects
    past_messages = history_to_messages(chat_history)

    messages = [SystemMessage(content="You are a helpful assistant.")]
    messages.extend(past_messages)
    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)

    state["answer"] = response.content
    return state