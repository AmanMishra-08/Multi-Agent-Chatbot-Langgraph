import re
import traceback
from utils.history import add_turn

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from config import GROQ_API_KEY
from state import ChatState


vision_llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="qwen/qwen3.6-27b",   # Change this if you use another vision model
    temperature=0.3,
    max_tokens=4096,
)


def vision_node(state: ChatState) -> ChatState:
    question = state.get("standalone_question") or state.get("question")
    image_b64 = state.get("uploaded_image", "")

    # MIME type comes from app.py
    mime = state.get("uploaded_image_type", "image/jpeg")

    if not image_b64:
        state["answer"] = "No image was uploaded."
        return state

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": f"""
You are an image understanding assistant.

Answer ONLY the user's question.

If the image is a document, read the document carefully.

Question:
{question}
""",
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime};base64,{image_b64}"
                },
            },
        ]
    )

    try:
        response = vision_llm.invoke([message])

        description = str(response.content).strip()

        print("=" * 80)
        print(description)
        print("=" * 80)

        # Remove reasoning if present
        if "<think>" in description:
            description = re.sub(
                r"<think>.*?</think>",
                "",
                description,
                flags=re.DOTALL,
            ).strip()

        # If nothing remains after removing reasoning
        if not description:
            description = "The model did not return a usable answer."

    except Exception:
        traceback.print_exc()
        description = "Sorry, I couldn't analyze that image."

    state["image_description"] = description
    state["answer"] = description

    state["chat_history"] = add_turn(state.get("chat_history", []), question, description)

    return state