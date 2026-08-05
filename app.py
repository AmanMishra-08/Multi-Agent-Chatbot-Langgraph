import streamlit as st
import base64
from graph import graph
from pathlib import Path
from stt import speech_to_text

st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide"
)

st.title(" Intelligent AI Chatbot")


# Custom CSS for better layout
st.markdown("""
<style>
/* Give space so the fixed chat input doesn't cover messages */
.main .block-container {
    padding-bottom: 160px;
}

/* Compact footer controls */
.footer-tools {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 72px; /* sits just above st.chat_input */
    background: var(--background-color);
    border-top: 1px solid rgba(128,128,128,0.18);
    padding: 10px 18px;
    z-index: 999;
}
</style>
""", unsafe_allow_html=True)

ROUTE_LABELS = {
    "llm": "🧠 LLM",
    "rag": "📚 RAG (Documents)",
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

if "voice_key" not in st.session_state:
    st.session_state.voice_key = 0

if "voice_processed" not in st.session_state:
    st.session_state.voice_processed = False    

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

if "input_mode" not in st.session_state:
    st.session_state.input_mode = "text"  # "text", "image", "voice"

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

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
# Helper: Process question through graph
# -------------------------
def process_question(question_text, uploaded_image_file=None):
    """Process a question through the LangGraph"""
    
    # Detect whether this is a genuinely NEW upload
    is_new_image_upload = False
    if uploaded_image_file is not None:
        current_file_id = (
            uploaded_image_file.file_id 
            if hasattr(uploaded_image_file, "file_id") 
            else uploaded_image_file.name
        )
        if current_file_id != st.session_state.active_image_file_id:
            is_new_image_upload = True
            st.session_state.active_image_file_id = current_file_id
            st.session_state.active_image_b64 = base64.b64encode(
                uploaded_image_file.getvalue()
            ).decode("utf-8")

    # Display the user's message immediately
    with st.chat_message("user"):
        st.markdown(question_text)
        user_image_placeholder = st.empty()

    # Prepare state for LangGraph
    state = {
        "question": question_text,
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

    # Update session state from result
    st.session_state.chat_history = result.get(
        "chat_history", st.session_state.chat_history
    )
    st.session_state.last_image_subject = result.get(
        "last_image_subject", st.session_state.last_image_subject
    )
    st.session_state.current_topic = result.get(
        "current_topic", st.session_state.current_topic
    )
    st.session_state.last_route = result.get("last_route", route)

    # Handle vision image preview
    image_preview_to_store = None
    if route == "vision" and uploaded_image_file is not None:
        with user_image_placeholder:
            st.image(uploaded_image_file, width=200)
        image_preview_to_store = uploaded_image_file

    # Store user message
    st.session_state.messages.append({
        "role": "user",
        "content": question_text,
        "uploaded_image_preview": image_preview_to_store,
    })

    # Auto-clear image if route is not vision
    if route != "vision" and st.session_state.active_image_b64:
        st.session_state.active_image_b64 = ""
        st.session_state.active_image_file_id = None
        st.session_state.uploader_key += 1

    # Display assistant response
    with st.chat_message("assistant"):
        st.caption(ROUTE_LABELS.get(route, route))
        st.markdown(answer)

        if generated_images:
            cols = st.columns(min(4, len(generated_images)))
            for i, image_url in enumerate(generated_images):
                with cols[i % len(cols)]:
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

    # Store assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "route": route,
        "images": images,
        "generated_images": generated_images,
    })

    return

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
                    st.image(image_url, width=400)

        if message.get("uploaded_image_preview") is not None:
            st.image(message["uploaded_image_preview"], width=200)

# -------------------------
# Footer Input Area (ChatGPT-style)
# -------------------------
st.divider()
st.markdown("### Input Area")

# Footer tools (Image + Voice)
tool_col1, tool_col2 = st.columns([1, 1])

with tool_col1:
    uploaded_file = st.file_uploader(
        "📎 Upload image",
        type=["png", "jpg", "jpeg"],
        label_visibility="collapsed",
        key=f"uploader_{st.session_state.uploader_key}"
    )

with tool_col2:
    audio = st.audio_input(
        "🎤 Speak",
        label_visibility="collapsed",
        key=f"voice_input_{st.session_state.voice_key}"
    )

# Clear image button
if uploaded_file is not None:
    clear_col1, clear_col2 = st.columns([5, 1])
    with clear_col2:
        if st.button("❌ Clear", key="clear_footer_img"):
            st.session_state.uploader_key += 1
            st.session_state.active_image_b64 = ""
            st.session_state.active_image_file_id = None
            st.rerun()

# -------------------------
# Voice Processing
# -------------------------
if audio is not None:
    audio_path = Path("audio/input.wav")
    audio_path.parent.mkdir(exist_ok=True)

    with open(audio_path, "wb") as f:
        f.write(audio.getvalue())

    with st.spinner("🔄 Converting speech to text..."):
        user_text = speech_to_text(str(audio_path))

    if user_text and user_text.strip():
        process_question(user_text, uploaded_file)

    # Reset the audio widget so the same recording is not processed again
    st.session_state.voice_key += 1
    st.rerun()
# -------------------------
# Fixed Bottom Text Input
# -------------------------
question = st.chat_input("Ask me anything...")

if question:
    process_question(question, uploaded_file)
    st.rerun()