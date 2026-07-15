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
    question = state.get("standalone_question", state["question"])
    chat_history = state.get("chat_history", [])

    past_messages = history_to_messages(chat_history)

    messages = [
        SystemMessage(
            content="""You are an Intelligent AI Chatbot created by Aman Mishra.

You are an AI assistant built using:
- LangGraph
- LangChain
- RAG
- FAISS
- Groq LLM
- Web Search

If someone asks:
- "Who made you?"
- "Who built you?"
- "Who designed you?"
- "Who developed you?"

Reply that you were created by Aman Mishra.

Do not claim you were created by Meta, OpenAI, Anthropic, or any other company.
"""
        )
    ]

    messages.extend(past_messages)
    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)

    state["answer"] = response.content
    
    # 🌟 FIX: Clear the sticky image subject during standard LLM chat turns
    state["last_image_subject"] = ""

    return state