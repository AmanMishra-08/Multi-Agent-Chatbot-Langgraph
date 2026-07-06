from langchain_community.vectorstores import FAISS

from config import VECTOR_DB_PATH
from rag.loader import load_pdfs
from rag.splitter import split_documents
from rag.embeddings import get_embedding_model


def build_vectorstore(data_folder: str):
    """
    Full pipeline: load PDFs -> split into chunks -> embed ->
    save FAISS index to disk. Called once by ingest.py.
    """
    documents = load_pdfs(data_folder)
    chunks = split_documents(documents)

    embeddings = get_embedding_model()
    vectorstore = FAISS.from_documents(chunks, embeddings)

    vectorstore.save_local(VECTOR_DB_PATH)
    print(f"✅ Vectorstore saved to '{VECTOR_DB_PATH}'")

    return vectorstore