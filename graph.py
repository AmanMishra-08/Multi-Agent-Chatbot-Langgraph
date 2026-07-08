from langgraph.graph import StateGraph, START, END

from state import ChatState

from nodes.rewrite import rewrite_query_node
from nodes.router import router_node
from nodes.llm import llm_node
from nodes.rag import rag_node
from nodes.web import web_node
from nodes.answer import answer_node


graph_builder = StateGraph(ChatState)

graph_builder.add_node("rewrite", rewrite_query_node)
graph_builder.add_node("router", router_node)
graph_builder.add_node("llm", llm_node)
graph_builder.add_node("rag", rag_node)
graph_builder.add_node("web", web_node)
graph_builder.add_node("answer", answer_node)

# Entry point: every run starts at the rewrite node now
graph_builder.add_edge(START, "rewrite")
graph_builder.add_edge("rewrite", "router")

graph_builder.add_conditional_edges(
    "router",
    lambda state: state["route"],
    {
        "llm": "llm",
        "rag": "rag",
        "web": "web",
    },
)

graph_builder.add_edge("llm", "answer")
graph_builder.add_edge("rag", "answer")
graph_builder.add_edge("web", "answer")

graph_builder.add_edge("answer", END)

graph = graph_builder.compile()