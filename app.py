import streamlit as st

from graph import graph

st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Intelligent AI Chatbot")

# Labels shown for each route, so the badge looks nice
ROUTE_LABELS = {
    "llm": "🧠 LLM",
    "rag": "📄 RAG (documents)",
    "web": "🌐 Web search",
}

# Messages shown on screen
if "messages" not in st.session_state:
    st.session_state.messages = []

# Actual memory passed into LangGraph on every turn
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Show the route badge only for assistant messages that have one
        if message["role"] == "assistant" and message.get("route"):
            st.caption(ROUTE_LABELS.get(message["route"], message["route"]))
        st.markdown(message["content"])

# User input
question = st.chat_input("Ask me anything...")

if question:

    # Display user message
    st.chat_message("user").markdown(question)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    # Initial LangGraph state — chat_history comes from session_state,
    # NOT an empty list, so the graph remembers past turns.
    state = {
        "question": question,
        "route": "",
        "documents": [],
        "answer": "",
        "chat_history": st.session_state.chat_history
    }

    # Run LangGraph
    result = graph.invoke(state)

    answer = result["answer"]
    route = result["route"]

    # Save the updated memory (built by nodes/answer.py) back
    # into session_state so the NEXT question sees it.
    st.session_state.chat_history = result["chat_history"]

    # Display assistant message with the route badge on top
    with st.chat_message("assistant"):
        st.caption(ROUTE_LABELS.get(route, route))
        st.markdown(answer)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "route": route
        }
    )