import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Disable telemetry to avoid sandboxed network latency or warnings
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_SERVER_NOOP_TELEMETRY"] = "True"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma_db"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Presentation Content Builder AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Storage paths
    UPLOAD_DIRECTORY: str = str(UPLOAD_DIR)
    CHROMA_DIRECTORY: str = str(CHROMA_DIR)

    # Chunking configurations
    DEFAULT_CHUNK_SIZE: int = 800
    DEFAULT_CHUNK_OVERLAP: int = 150

    # Embedding configurations
    EMBEDDING_PROVIDER: str = "local"  # 'local', 'openai', or 'fast_fallback'
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # LLM Configurations
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_OPENAI_MODEL: str = "gpt-4o"
    DEFAULT_GEMINI_MODEL: str = "gemini-2.0-flash"


settings = Settings()
