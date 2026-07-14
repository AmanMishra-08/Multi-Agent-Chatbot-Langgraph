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
    - Biases results toward faces/portraits when the query looks like
      a person's name, filtering out movie posters, DVD collections, etc.
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
    # Detect if this looks like a person's name search
    # (e.g. "Jim Carrey", "Virat Kohli") -> apply a face filter so
    # Google prioritizes portrait photos over posters/DVD collections/
    # book covers/merchandise.
    # Heuristic: 2-4 capitalized-looking words, no digits, no common
    # object/place keywords.
    # ------------------------------------
    NON_PERSON_HINTS = [
        "building", "tower", "mountain", "bridge", "temple", "beach",
        "car", "dog", "cat", "flower", "lion", "tiger", "leopard",
        "logo", "chart", "map", "food", "recipe", "landscape",
    ]
    # Strip a leading count number (e.g. "5 jim carrey" -> "jim carrey")
    # before running person-detection, since our own numeric shortcut
    # prepends counts to the query and was defeating the digit check.
    subject_only = re.sub(r"^\d+\s+", "", clean_query).strip()

    words = subject_only.split()
    looks_like_person = (
        1 <= len(words) <= 4
        and not any(char.isdigit() for char in subject_only)
        and not any(hint in subject_only.lower() for hint in NON_PERSON_HINTS)
    )

    search_params = {
        "q": clean_query,
        "engine": "google_images",
        "api_key": SERPAPI_KEY,
    }

    if looks_like_person:
        # Bias toward face/portrait photos — same as Google Images'
        # Tools -> Type -> Faces filter.
        search_params["tbs"] = "itp:face"
        print(f"[image_search] Applying face filter for: {clean_query!r}")

    # ------------------------------------
    # Search Images
    # ------------------------------------
    images = []

    try:
        search = GoogleSearch(search_params)

        results = search.get_dict()

        seen_urls = set()

        for item in results.get("images_results", []):

            if len(images) >= num_images:
                break

            url = item.get("original") or item.get("thumbnail")

            if not url or url in seen_urls:
                continue

            seen_urls.add(url)

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