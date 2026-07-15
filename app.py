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
    "vision": "👁️ Vision",
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

        # Only show the uploaded image on messages where it was
        # ACTUALLY used for vision -- not on every message that
        # happened to be sent while an image was still attached.
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
# User Input
# -------------------------
question = st.chat_input("Ask me anything...")

if question:

    # Detect whether this is a genuinely NEW upload -- evaluated HERE,
    # at the moment a question is actually submitted, not earlier when
    # the file first appeared in the widget (that happens on a separate
    # rerun with no question attached, so detecting "new" there would
    # get silently consumed before the user ever asks about it).
    is_new_image_upload = False
    if uploaded_file is not None:
        current_file_id = uploaded_file.file_id if hasattr(uploaded_file, "file_id") else uploaded_file.name
        if current_file_id != st.session_state.active_image_file_id:
            is_new_image_upload = True
            st.session_state.active_image_file_id = current_file_id
            st.session_state.active_image_b64 = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")

    # Display the user's TEXT immediately. The image (if any) is shown
    # in a placeholder that we only fill in AFTER we know the route --
    # this avoids showing an image on a message where it wasn't
    # actually used (e.g. "capital of india" while an old image is
    # still technically attached but irrelevant).
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

    # Only NOW, knowing the route, decide whether to show/save the
    # uploaded image alongside this message.
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

    # -------------------------
    # Auto-clear the image if the router decided this turn is NOT
    # about the image anymore (route != "vision"). This means the
    # NEXT message won't have the old image attached.
    # -------------------------
    if route != "vision" and st.session_state.active_image_b64:
        print("[app] Route changed away from vision -- clearing active image")
        st.session_state.active_image_b64 = ""
        st.session_state.active_image_file_id = None
        st.session_state.uploader_key += 1

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

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "route": route,
        "images": images,
    })

    st.rerun()