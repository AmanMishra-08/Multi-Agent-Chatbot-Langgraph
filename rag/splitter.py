def split_documents(documents: list) -> list:
    """
    Splits loaded documents into smaller overlapping chunks,
    so each chunk is small enough to embed meaningfully and
    retrieve precisely.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from config import CHUNK_SIZE, CHUNK_OVERLAP

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks.")
    return chunks