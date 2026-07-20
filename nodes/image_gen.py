import re
import urllib.parse

from state import ChatState


def image_gen_node(state: ChatState) -> ChatState:
    """
    Generate AI images using Pollinations.ai.

    Examples:
    - Generate a cat
    - Create an image of Iron Man
    - Draw a futuristic city
    - Generate 4 anime girls
    """

    question = state["standalone_question"]

    # -----------------------------
    # Number of images (default = 1)
    # -----------------------------
    num_images = 1

    match = re.search(r"\b(\d+)\b", question)

    if match:
        num_images = max(1, min(int(match.group(1)), 4))

    # -----------------------------
    # Clean the prompt
    # -----------------------------
    prompt = re.sub(
        r"^(generate|genarate|create|draw|make)\s+",
        "",
        question,
        flags=re.IGNORECASE,
    )

    prompt = re.sub(
        r"^(an?|the)\s+",
        "",
        prompt,
        flags=re.IGNORECASE,
    )

    prompt = re.sub(
        r"^(image|picture|photo)\s+(of\s+)?",
        "",
        prompt,
        flags=re.IGNORECASE,
    )
    prompt = re.sub(r"^of\s+", "", prompt, flags=re.IGNORECASE)

    prompt = re.sub(
        r"\b\d+\b",
        "",
        prompt,
    )

    prompt = re.sub(
        r"\b(images|image|photos|photo|pictures|picture)\b",
        "",
        prompt,
        flags=re.IGNORECASE,
    )

    prompt = " ".join(prompt.split())

    if not prompt:
        prompt = question

    encoded_prompt = urllib.parse.quote(prompt)

    generated_images = []

    for seed in range(num_images):
        image_url = (
            f"https://image.pollinations.ai/prompt/"
            f"{encoded_prompt}?seed={seed}"
        )
        generated_images.append(image_url)

    state["generated_images"] = generated_images

    # 🌟 FIX HERE: Save the cleaned prompt subject back to the state!
    # This guarantees that the rewriter node knows what the user was generating.
    state["last_image_subject"] = prompt

    state["answer"] = (
        f"🎨 Generated {len(generated_images)} image(s) for:\n\n"
        f"**{prompt}**"
    )

    return state