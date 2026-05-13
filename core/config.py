from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Lorebait API"
    environment: str = "development"
    log_level: str = "INFO"

    data_dir: Path = Field(default=Path(".lorebait_data"))
    database_url: str | None = None
    cors_origins: str = "http://localhost:3000"

    llm_provider: Literal["openai", "ollama"] = "ollama"
    embedding_provider: Literal["openai", "ollama"] | None = None

    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    ollama_embedding_model: str = "nomic-embed-text"

    chunk_size: int = 1000
    chunk_overlap: int = 150
    retrieval_k: int = 4
    lancedb_table: str = "documents"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def resolved_data_dir(self) -> Path:
        return self.data_dir.expanduser().resolve()

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        db_path = self.resolved_data_dir / "lorebait.sqlite3"
        return f"sqlite+aiosqlite:///{db_path.as_posix()}"

    @property
    def resolved_embedding_provider(self) -> Literal["openai", "ollama"]:
        return self.embedding_provider or self.llm_provider

    @property
    def lancedb_uri(self) -> str:
        return str((self.resolved_data_dir / "lancedb").resolve())


@lru_cache
def get_settings() -> Settings:
    return Settings()
