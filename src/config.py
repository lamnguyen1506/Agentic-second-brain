"""Type-safe configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 500
    chunk_overlap: int = 50

    # Vector Store
    chroma_persist_dir: str = "./chroma_db"
    collection_name: str = "knowledge_base"

    # Memory
    memory_db_path: str = "data/memory.db"

    # Agent
    llm_model: str = "anthropic:claude-sonnet-4-5"
    retrieval_top_k: int = 3
    use_memory: bool = True

    # Observability
    service_name: str = "second-brain"
    log_file: str = "logs/app.log"
    log_level: str = "INFO"


_settings: Settings | None = None


def get_settings() -> Settings:
    """Get cached settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
