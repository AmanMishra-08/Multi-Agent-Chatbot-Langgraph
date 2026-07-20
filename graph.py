from langgraph.graph import StateGraph, START, END

from state import ChatState

from nodes.rewrite import rewrite_query_node
from nodes.router import router_node
from nodes.llm import llm_node
from nodes.rag import rag_node
from nodes.web import web_node
from nodes.image_search import image_search_node
from nodes.image_gen import image_gen_node 
from nodes.answer import answer_node
from nodes.vision import vision_node


graph_builder = StateGraph(ChatState)

graph_builder.add_node("rewrite", rewrite_query_node)
graph_builder.add_node("router", router_node)
graph_builder.add_node("llm", llm_node)
graph_builder.add_node("rag", rag_node)
graph_builder.add_node("web", web_node)
graph_builder.add_node("image_search", image_search_node)
graph_builder.add_node("image_gen", image_gen_node) 
graph_builder.add_node("answer", answer_node)
graph_builder.add_node("vision", vision_node)

graph_builder.add_edge(START, "rewrite")
graph_builder.add_edge("rewrite", "router")

graph_builder.add_conditional_edges(
    "router",
    lambda state: state["route"],
    {
        "llm": "llm",
        "rag": "rag",
        "web": "web",
        "image_search": "image_search",
        "image_gen": "image_gen",
        "vision": "vision",
    },
)

graph_builder.add_edge("llm", "answer")
graph_builder.add_edge("rag", "answer")
graph_builder.add_edge("web", "answer")

graph_builder.add_edge("image_search", END)

graph_builder.add_edge("image_gen", END) 

graph_builder.add_edge("answer", END)

graph_builder.add_edge("vision", END)

graph = graph_builder.compile()