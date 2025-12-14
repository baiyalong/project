import os

class Settings:
    # Model Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://heritage_user:heritage_password@localhost:5432/heritage")

    # Vector Store Configuration
    CHROMA_HOST = os.getenv("CHROMA_HOST")
    CHROMA_PORT = os.getenv("CHROMA_PORT", "8002")
    CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_db")
    COLLECTION_NAME = "heritage_knowledge_base"

settings = Settings()
