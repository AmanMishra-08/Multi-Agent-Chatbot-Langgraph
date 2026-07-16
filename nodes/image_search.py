import re
from langchain_community.utilities import SerpAPIWrapper
from state import ChatState
from config import SERPAPI_KEY  # Ensure this matches your config export

def image_search_node(state: ChatState) -> ChatState:
    query = state.get("standalone_question") or state["question"]
    
    print("[image_search] Received Query ->", query)
    
    # 1. Parse image count request
    num_images = 1
    count_match = re.search(r"\b(\d+)\b", query)
    if count_match:
        num_images = int(count_match.group(1))
    
    # 2. Clean up search term to get the precise subject target
    search_term = query

    clean_match = re.search(
        r"(?:photos?|images?|pics?|pictures?)\s+of\s+(.+)$",
        query,
        re.IGNORECASE,
    )

    if clean_match:
        # "images of ms dhoni"
        search_term = clean_match.group(1).strip()

    else:
        # Remove "4 photo"
        search_term = re.sub(
            r"^\d+\s+(?:photos?|images?|pics?|pictures?)\s*$",
            "",
            query,
            flags=re.IGNORECASE,
        ).strip()

        # If nothing remains, use previous subject
        if not search_term:
            search_term = state.get("last_image_subject", "")
    
    # Update last_image_subject so it tracks across state conversational turns
    state["last_image_subject"] = search_term

    # 3. Execute Search using LangChain Community Wrapper
    try:
        # 🌟 FIX: Explicitly pass the API key to the parameter named 'serpapi_api_key'
        search = SerpAPIWrapper(
            serpapi_api_key=SERPAPI_KEY, 
            params={"engine": "google_images"}
        )
        
        # .results() returns the raw JSON dictionary structure from SerpAPI
        results = search.results(search_term)
        images_results = results.get("images_results", [])
        print(f"[image_search_node] Found {len(images_results)} raw image(s)")
        
        # 4. Map API response data structural keys precisely for app.py
        fetched = []
        for img in images_results[:num_images]:
            fetched.append({
                "url": img.get("original") or img.get("thumbnail"),  # Maps directly to app.py image["url"]
                "title": img.get("title", "Image"),
                "link": img.get("link")
            })
            
        state["fetched_images"] = fetched
        print(f"[image_search_node] Successfully saved {len(fetched)} parsed image(s) to state")
        
    except Exception as e:
        print(f"[image_search_node] Search Error: {e}")
        state["fetched_images"] = []

    # 5. Provide a text answer fallback to satisfy the graph flow display
    state["answer"] = f"Here are the images you requested for **{search_term}**:"
    return state