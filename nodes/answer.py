from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage

from config import GROQ_API_KEY, LLM_MODEL
from state import ChatState
from prompts.answer_prompt import ANSWER_PROMPT
from utils.history import add_turn


llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=LLM_MODEL,
    temperature=0.3,
)


def answer_node(state: ChatState) -> ChatState:
    """
    Final node.

    - image_search and llm routes: answer is already complete, skip polish.
    - web and rag routes: light polish pass, since these blend search
      results/retrieved chunks and benefit most from a coherence pass.
    - Conversation history is updated in all cases.
    """

    question = state.get("standalone_question", state["question"])
    draft_answer = state["answer"]
    route = state["route"]
    chat_history = state.get("chat_history", [])

    # Skip polishing for routes that already produce a clean, complete answer
    if route in ("image_search", "llm"):
        state["chat_history"] = add_turn(chat_history, question, draft_answer)
        state["answer"] = draft_answer
        return state

    # Polish web/rag answers — these blend external content and benefit
    # most from a coherence/formatting pass
    prompt = ANSWER_PROMPT.format(draft_answer=draft_answer)
    response = llm.invoke([SystemMessage(content=prompt)])
    final_answer = response.content.strip()

    state["answer"] = final_answer
    state["chat_history"] = add_turn(chat_history, question, final_answer)

    return state