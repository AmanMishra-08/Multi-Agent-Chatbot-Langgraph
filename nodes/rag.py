from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from config import GROQ_API_KEY, LLM_MODEL
from state import ChatState
from utils.history import history_to_messages
from rag.retriever import retrieve


llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=LLM_MODEL,
    temperature=0.3,
)


def rag_node(state: ChatState) -> ChatState:
    question = state["question"]
    chat_history = state.get("chat_history", [])

    # Retrieve relevant chunks from the FAISS index
    context_chunks = retrieve(question)
    context = "\n\n".join(context_chunks)

    system_prompt = (
        "You are a helpful assistant. Answer the user's question using "
        "ONLY the context below. If the answer isn't in the context, "
        "say you don't have that information.\n\n"
        f"Context:\n{context}"
    )

    past_messages = history_to_messages(chat_history)

    messages = [SystemMessage(content=system_prompt)]
    messages.extend(past_messages)
    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)

    state["documents"] = context_chunks
    state["answer"] = response.content
    return state