import os
from dotenv import load_dotenv

load_dotenv()

# =============================
# API Keys
# =============================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# =============================
# Models
# =============================

LLM_MODEL = "llama-3.3-70b-versatile"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# =============================
# RAG settings
# =============================

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 3

# =============================
# Paths
# =============================

DATA_FOLDER = "data"
VECTOR_DB_PATH = "faiss_index"

# =============================
# Memory
# =============================

MAX_HISTORY_MESSAGES = 20