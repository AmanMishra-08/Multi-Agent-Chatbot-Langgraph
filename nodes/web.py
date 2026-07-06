from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from config import GROQ_API_KEY, LLM_MODEL
from state import ChatState
from utils.history import history_to_messages
from web.search import search


llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=LLM_MODEL,
    temperature=0.3,
)


def web_node(state: ChatState) -> ChatState:
    question = state["question"]
    chat_history = state.get("chat_history", [])

    # Run a web search via Tavily
    search_results = search(question)
    context = "\n\n".join(search_results)

    system_prompt = (
        "You are a helpful assistant. Use the web search results below "
        "to answer the user's question accurately and concisely. "
        "Mention that the information comes from a web search if relevant.\n\n"
        f"Search results:\n{context}"
    )

    past_messages = history_to_messages(chat_history)

    messages = [SystemMessage(content=system_prompt)]
    messages.extend(past_messages)
    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)

    state["documents"] = search_results
    state["answer"] = response.content
    return state