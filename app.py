import streamlit as st
import base64
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
    "image_gen": "🎨 Image Generation",
    "vision": "👁️ Vision",
}

# -------------------------
# Session State
# -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "active_image_b64" not in st.session_state:
    st.session_state.active_image_b64 = ""

if "active_image_file_id" not in st.session_state:
    st.session_state.active_image_file_id = None

if "last_image_subject" not in st.session_state:
    st.session_state.last_image_subject = ""

if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""

if "last_route" not in st.session_state:
    st.session_state.last_route = ""

# -------------------------
# Helper: safely display an image
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
        generated_images = message.get("generated_images", [])

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

        if generated_images:
            cols = st.columns(min(4, len(generated_images)))
            for i, image_url in enumerate(generated_images):
                with cols[i % len(cols)]:
                    # FIX 1: Replaced use_container_width=True with width=400
                    st.image(image_url, width=400)

        if message.get("uploaded_image_preview") is not None:
            st.image(message["uploaded_image_preview"], width=200)

# -------------------------
# Image Upload (optional, used for the vision route)
# -------------------------
uploaded_file = st.file_uploader(
    "Upload an image (optional)",
    type=["png", "jpg", "jpeg"],
    key=f"uploader_{st.session_state.uploader_key}"
)

if uploaded_file is not None:
    if st.button("❌ Clear image"):
        st.session_state.uploader_key += 1
        st.session_state.active_image_b64 = ""
        st.session_state.active_image_file_id = None
        st.rerun()

# -------------------------
# User Input & Processing
# -------------------------
question = st.chat_input("Ask me anything...")

if question:

    # Detect whether this is a genuinely NEW upload
    is_new_image_upload = False
    if uploaded_file is not None:
        current_file_id = uploaded_file.file_id if hasattr(uploaded_file, "file_id") else uploaded_file.name
        if current_file_id != st.session_state.active_image_file_id:
            is_new_image_upload = True
            st.session_state.active_image_file_id = current_file_id
            st.session_state.active_image_b64 = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")

    # Display the user's TEXT immediately
    with st.chat_message("user"):
        st.markdown(question)
        user_image_placeholder = st.empty()

    # Initial state
    state = {
        "question": question,
        "standalone_question": "",
        "route": "",
        "rag_context": [],
        "web_context": [],
        "retrieved_context": "",
        "answer": "",
        "chat_history": st.session_state.chat_history,
        "fetched_images": [],
        "generated_images": [], 
        "last_image_subject": st.session_state.last_image_subject,
        "current_topic": st.session_state.current_topic,
        "last_route": st.session_state.last_route,
        "uploaded_image": st.session_state.active_image_b64,
        "image_description": "",
        "is_new_image_upload": is_new_image_upload,
    }

    # Invoke LangGraph
    result = graph.invoke(state)

    answer = result["answer"]
    route = result["route"]
    images = result.get("fetched_images", [])
    generated_images = result.get("generated_images", [])

    st.session_state.chat_history = result.get(
        "chat_history",
        st.session_state.chat_history,
    )

    st.session_state.last_image_subject = result.get(
        "last_image_subject",
        st.session_state.last_image_subject,
    )

    st.session_state.current_topic = result.get(
        "current_topic",
        st.session_state.current_topic,
    )

    st.session_state.last_route = result.get(
        "last_route",
        route,
    ) 

    # Handle active vision image preview tracking
    image_preview_to_store = None
    if route == "vision" and uploaded_file is not None:
        with user_image_placeholder:
            st.image(uploaded_file, width=200)
        image_preview_to_store = uploaded_file

    st.session_state.messages.append({
        "role": "user",
        "content": question,
        "uploaded_image_preview": image_preview_to_store,
    })

    # Auto-clear the image if the router decided this turn is NOT about vision anymore
    if route != "vision" and st.session_state.active_image_b64:
        st.session_state.active_image_b64 = ""
        st.session_state.active_image_file_id = None
        st.session_state.uploader_key += 1

    # -------------------------
    # Assistant Response
    # -------------------------
    with st.chat_message("assistant"):
        st.caption(ROUTE_LABELS.get(route, route))
        st.markdown(answer)

        if generated_images:
            cols = st.columns(min(4, len(generated_images)))
            for i, image_url in enumerate(generated_images):
                with cols[i % len(cols)]:
                    # FIX 2: Replaced use_container_width=True with width=400
                    st.image(image_url, width=400)

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

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "route": route,
        "images": images,
        "generated_images": generated_images,
    })

    st.rerun()