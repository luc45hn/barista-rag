import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # LLMs
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # App
    APP_NAME: str = "Barista IA"

    # RAG
    KNOWLEDGE_BASE_DIR: str = "knowledge_base"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    TOP_K_RESULTS: int = 4

    # LLM config
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 1024

    @classmethod
    def validate(cls) -> bool:
        missing = []
        if not cls.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not cls.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        if not cls.GOOGLE_API_KEY and not cls.GROQ_API_KEY:
            missing.append("GOOGLE_API_KEY o GROQ_API_KEY")
        if missing:
            raise ValueError(f"Variables de entorno faltantes: {', '.join(missing)}")
        return True
