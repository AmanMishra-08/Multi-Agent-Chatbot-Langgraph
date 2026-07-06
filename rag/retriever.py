from langchain_community.vectorstores import FAISS

from config import VECTOR_DB_PATH, TOP_K
from rag.embeddings import get_embedding_model


# Loaded once when this module is imported, so the FAISS index
# isn't reloaded from disk on every single question.
_embeddings = get_embedding_model()

_vectorstore = FAISS.load_local(
    VECTOR_DB_PATH,
    _embeddings,
    allow_dangerous_deserialization=True,
)


def retrieve(question: str) -> list[str]:
    """
    Searches the FAISS index for the TOP_K chunks most relevant
    to the question. Returns a list of plain text strings.
    """
    docs = _vectorstore.similarity_search(question, k=TOP_K)
    return [doc.page_content for doc in docs]