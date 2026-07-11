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

CRITICAL RULE 1: Always resolve pronouns and vague references ("they", "it", "this") using the MOST RECENT topic in the history — the last 1-2 exchanges — NOT older topics from earlier in the conversation.

CRITICAL RULE 2: Questions like "when did this happen", "where did this happen", "who did this" almost always refer to the MAIN EVENT/INCIDENT being discussed throughout the conversation — not a minor detail mentioned in the most recent answer (like a side-comment about marriage, reactions, or opinions). Identify the core event being discussed across the whole recent exchange, and resolve "this" to THAT event.

Example: 
History discusses "the Empire State Building climbing incident", then a follow-up answer mentions "they got engaged".
User asks: "when did this happen"
Correct standalone question: "When did the Empire State Building climbing incident happen?"
WRONG: "When did they get married?" (this incorrectly latches onto a minor detail, not the main event)

If the question is already standalone, return it unchanged.
Return ONLY the rewritten question — no explanation, no preamble, no quotes."""


def rewrite_query_node(state: ChatState) -> ChatState:
    question = state["question"].strip().strip('"').strip("'").strip()
    chat_history = state.get("chat_history", [])
    last_subject = state.get("last_image_subject", "")

    # DETERMINISTIC SHORTCUT 1: short numeric image follow-ups
    is_short_image_followup = re.fullmatch(
        r"(give me |show me |get me |fetch )?\d+\s*image(s)?",
        question.strip().lower()
    )
    if is_short_image_followup and last_subject:
        count_match = re.search(r"\d+", question)
        count = count_match.group() if count_match else "1"
        rewritten = f"{count} images of {last_subject}"
        print(f"[rewrite_query_node] deterministic shortcut: {question!r} -> {rewritten!r}")
        state["standalone_question"] = rewritten
        return state

    # DETERMINISTIC SHORTCUT 2: fully self-contained requests need no rewrite.
    # If the question has no pronouns/vague references AND is reasonably
    # specific (5+ words, or contains an image request), it's already
    # standalone — skip the LLM to avoid it "helpfully" over-rewriting
    # and getting confused by history/prompt examples.
    PRONOUNS = ["they", "them", "their", "this", "that", "it", "he", "she", "his", "her"]
    has_pronoun = any(f" {p} " in f" {question.lower()} " for p in PRONOUNS)
    if not has_pronoun and not chat_history:
        state["standalone_question"] = question
        return state

    if not has_pronoun and len(question.split()) >= 4:
        print(f"[rewrite_query_node] self-contained, no rewrite needed: {question!r}")
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