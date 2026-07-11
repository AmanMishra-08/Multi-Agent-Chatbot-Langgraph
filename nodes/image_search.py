import re
from serpapi import GoogleSearch

from config import SERPAPI_KEY
from state import ChatState


def image_search_node(state: ChatState) -> ChatState:
    """
    Searches Google Images using SerpAPI and returns image metadata.

    Features:
    - Supports "give me 4 images"
    - Cleans the search query
    - Remembers the last searched image subject
    """

    question = state["standalone_question"]

    # ------------------------------------
    # Number of images requested
    # ------------------------------------
    match = re.search(r"\b(\d+)\b", question)

    if match:
        num_images = int(match.group(1))
    else:
        num_images = 1

    num_images = max(1, min(num_images, 10))

    # ------------------------------------
    # Clean the search query
    # ------------------------------------
    clean_query = re.sub(
        r"\b(show|display|give|find|get|fetch|me|image|images|photo|photos|picture|pictures|pic|pics|of|a|an|the)\b",
        "",
        question,
        flags=re.IGNORECASE,
    )

    clean_query = " ".join(clean_query.split())

    # If rewrite couldn't determine the subject,
    # use the previous searched subject.
    if clean_query:
        state["last_image_subject"] = clean_query
    else:
        clean_query = state.get("last_image_subject", question)

    print(f"[image_search] Search Query -> {clean_query}")

    # ------------------------------------
    # Search Images
    # ------------------------------------
    images = []

    try:
        search = GoogleSearch(
            {
                "q": clean_query,
                "engine": "google_images",
                "api_key": SERPAPI_KEY,
            }
        )

        results = search.get_dict()

        for item in results.get("images_results", [])[:num_images]:

            url = item.get("original") or item.get("thumbnail")

            if not url:
                continue

            images.append(
                {
                    "url": url,
                    "title": item.get("title", "No title"),
                    "source": item.get("source", "Unknown"),
                    "link": item.get("link", ""),
                }
            )

    except Exception as e:
        print(f"[image_search_node] ERROR: {e}")
        images = []

    print(f"[image_search_node] Found {len(images)} image(s)")

    # ------------------------------------
    # Update State
    # ------------------------------------
    state["fetched_images"] = images

    if images:
        state["answer"] = (
            f'Here {"are" if len(images) > 1 else "is"} '
            f'{len(images)} image(s) for "{clean_query}":'
        )
    else:
        state["answer"] = f'No images found for "{clean_query}".'

    return state