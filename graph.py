from langgraph.graph import StateGraph, START, END

from state import ChatState

from nodes.router import router_node
from nodes.llm import llm_node
from nodes.rag import rag_node
from nodes.web import web_node
from nodes.answer import answer_node


graph_builder = StateGraph(ChatState)

graph_builder.add_node("router", router_node)
graph_builder.add_node("llm", llm_node)
graph_builder.add_node("rag", rag_node)
graph_builder.add_node("web", web_node)
graph_builder.add_node("answer", answer_node)

# Entry point: every run starts at the router
graph_builder.add_edge(START, "router")

# router_node sets state["route"] to "llm", "rag", or "web".
# This conditional edge reads that value and picks the next node.
graph_builder.add_conditional_edges(
    "router",
    lambda state: state["route"],
    {
        "llm": "llm",
        "rag": "rag",
        "web": "web",
    },
)
# it return state[llm/rag/web]
# All three branches funnel into "answer" to polish + save memory
graph_builder.add_edge("llm", "answer")
graph_builder.add_edge("rag", "answer")
graph_builder.add_edge("web", "answer")

graph_builder.add_edge("answer", END)

# Compile into a runnable graph object — app.py imports this
graph = graph_builder.compile()