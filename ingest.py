from rag.vectorstore import build_vectorstore
from config import DATA_FOLDER


if __name__ == "__main__":
    build_vectorstore(DATA_FOLDER)

    #Build the FAISS vector database from your PDFs.

 #Run me (simple flow)
 #    │
 #    ▼
#build_vectorstore()   