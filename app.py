import streamlit as st

from graph import graph

st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Intelligent AI Chatbot")

ROUTE_LABELS = {
    "llm": "🧠 LLM",
    "rag": "📄 RAG (Documents)",
    "web": "🌐 Web Search",
    "image_search": "🖼️ Image Search",
}

# -------------------------
# Session State
# -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_image_subject" not in st.session_state:
    st.session_state.last_image_subject = ""

# -------------------------
# Helper: safely display an image, falling back gracefully if the
# hotlinked URL is dead/blocked instead of showing a broken gray box.
# -------------------------
def safe_show_image(image, width=220):
    try:
        st.image(image["url"], width=width)
    except Exception:
        st.caption("⚠️ Image failed to load")
    st.caption(image.get("title", ""))

# -------------------------
# Display Previous Messages
# -------------------------
for msg_idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):

        if message["role"] == "assistant":
            st.caption(
                ROUTE_LABELS.get(
                    message.get("route", ""),
                    message.get("route", "")
                )
            )

        st.markdown(message["content"])

        images = message.get("images", [])

        if images:

            cols = st.columns(min(4, len(images)))

            for i, image in enumerate(images):
                with cols[i % len(cols)]:

                    safe_show_image(image)

                    if image.get("link"):
                        st.link_button(
                            "🔗 Open",
                            image["link"],
                            key=f"history_{msg_idx}_{i}_{image['url']}"
                        )

# -------------------------
# User Input
# -------------------------
question = st.chat_input("Ask me anything...")

if question:

    # Display user message
    with st.chat_message("user"):
        st.markdown(question)

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    # Initial state
    state = {
        "question": question,
        "route": "",
        "answer": "",
        "chat_history": st.session_state.chat_history,
        "last_image_subject": st.session_state.last_image_subject,
    }

    # Invoke LangGraph
    result = graph.invoke(state)

    answer = result["answer"]
    route = result["route"]
    images = result.get("fetched_images", [])

    st.session_state.chat_history = result.get("chat_history", [])
    st.session_state.last_image_subject = result.get(
        "last_image_subject", st.session_state.last_image_subject
    )

    # -------------------------
    # Assistant Response
    # -------------------------
    with st.chat_message("assistant"):

        st.caption(ROUTE_LABELS.get(route, route))

        st.markdown(answer)

        if images:

            cols = st.columns(min(4, len(images)))

            for i, image in enumerate(images):
                with cols[i % len(cols)]:

                    safe_show_image(image)

                    if image.get("link"):
                        st.link_button(
                            "🔗 Open",
                            image["link"],
                            key=f"current_{len(st.session_state.messages)}_{i}_{image['url']}"
                        )

    # Save assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "route": route,
        "images": images,
    })