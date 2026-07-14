import re

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from config import GROQ_API_KEY, LLM_MODEL
from state import ChatState
from utils.history import history_to_messages


llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=LLM_MODEL,
    temperature=0,
)


REWRITE_PROMPT = """Given the conversation history and the latest user question, rewrite the latest question into a short, standalone question (under 20 words) that makes sense without needing the history.

CRITICAL RULE 1: Always resolve pronouns and vague references -- this includes single-word pronouns ("they", "it", "this", "that") AND vague noun phrases ("the incident", "the event", "the match", "the mission", "the situation", "this story") -- using the MOST RECENT topic in the history -- the last 1-2 exchanges -- NOT older topics from earlier in the conversation.

CRITICAL RULE 2: Questions like "when did this happen", "what is the incident date", "where did this happen", "who did this" almost always refer to the MAIN EVENT/TOPIC being discussed throughout the conversation -- not a minor detail mentioned in the most recent answer. Identify the core event/topic being discussed across the whole recent exchange, and resolve the vague reference to THAT topic.

Example 1:
History discusses "the Empire State Building climbing incident", then a follow-up answer mentions "they got engaged".
User asks: "what is the incident date"
Correct standalone question: "What is the date of the Empire State Building climbing incident?"
WRONG: "What is the date of their engagement?"

CRITICAL RULE 3: If the question is ALREADY fully clear and self-contained -- meaning it names its own specific subject and has no pronoun or vague reference that depends on prior conversation -- you MUST return it completely unchanged, word for word. Do NOT invent new details, do NOT add assumptions, do NOT rephrase it. When uncertain whether something needs resolving, prefer returning the question unchanged over guessing.

Example 2:
User asks: "image of aman" (names its own subject -- nothing to resolve)
Correct standalone question: "image of aman" (unchanged)
WRONG: "Aman does not form question."

Return ONLY the rewritten question -- no explanation, no preamble, no quotes."""


def rewrite_query_node(state: ChatState) -> ChatState:
    question = state["question"].strip().strip('"').strip("'").strip()
    chat_history = state.get("chat_history", [])
    last_subject = state.get("last_image_subject", "")

    is_short_image_followup = re.fullmatch(
        r"(give me |show me |get me |fetch )?\d+\s*(image(s)?|photo(s)?|pic(s)?|picture(s)?)",
        question.strip().lower()
    )
    if is_short_image_followup and last_subject:
        count_match = re.search(r"\d+", question)
        count = count_match.group() if count_match else "1"
        rewritten = f"{count} images of {last_subject}"
        print(f"[rewrite_query_node] deterministic shortcut (numeric): {question!r} -> {rewritten!r}")
        state["standalone_question"] = rewritten
        return state

    has_pronoun_quick_check = any(
        f" {p} " in f" {question.lower()} "
        for p in ["they", "them", "their", "this", "that", "it", "he", "she", "his", "her"]
    )
    IMAGE_REQUEST_PATTERN = re.search(
        r"(image|photo|pic|picture)s?\s+of\s+\w+", question.lower()
    )
    if IMAGE_REQUEST_PATTERN and not has_pronoun_quick_check:
        print(f"[rewrite_query_node] deterministic shortcut (explicit image request): {question!r}")
        state["standalone_question"] = question
        return state

    if not chat_history:
        state["standalone_question"] = question
        return state

    recent_history = chat_history[-4:]

    messages = [SystemMessage(content=REWRITE_PROMPT)]
    messages.extend(history_to_messages(recent_history))
    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)
    rewritten = response.content.strip().strip('"')

    print(f"[rewrite_query_node] LLM rewrite: {question!r} -> {rewritten!r}")

    state["standalone_question"] = rewritten
    return state