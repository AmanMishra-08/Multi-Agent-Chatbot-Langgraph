def get_embedding_model():
    """
    Returns the embedding model used to convert text chunks into
    vectors. Defined in one place so both vectorstore.py (building
    the index) and retriever.py (searching it) use the exact same
    model — using different models for building vs. searching would
    silently break retrieval.
    """
    from langchain_huggingface import HuggingFaceEmbeddings
    from config import EMBEDDING_MODEL

    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)