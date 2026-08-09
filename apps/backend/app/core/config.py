"""
Configuration management module using Pydantic v2 BaseSettings.
Loads environment variables and enforces typing and validation rules.
"""

from typing import List, Literal, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings model powered by Pydantic v2."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App Metadata
    APP_NAME: str = Field(default="DSM-5 Psychiatry & Clinical Psychology AI Assistant")
    APP_ENV: Literal["development", "staging", "production", "testing"] = Field(
        default="development"
    )
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")
    API_V1_STR: str = Field(default="/api/v1")
    SECRET_KEY: str = Field(
        default="secret-key-change-in-production-min-32-chars-length"
    )

    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=["*"]
    )
    ALLOWED_HOSTS: List[str] = Field(default=["*"])

    # Database & Storage
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/dsm5_psychiatry"
    )
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # Supabase (Optional Cloud Storage & DB integration)
    SUPABASE_URL: Optional[str] = Field(default=None)
    SUPABASE_ANON_KEY: Optional[str] = Field(default=None)
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(default=None)
    SUPABASE_STORAGE_BUCKET: str = Field(default="documents")

    # Active AI Providers
    ACTIVE_LLM_PROVIDER: Literal[
        "openai", "anthropic", "google_gemini", "gemini", "groq", "openrouter", "ollama"
    ] = Field(default="groq")

    ACTIVE_EMBEDDING_PROVIDER: Literal[
        "openai", "bge", "e5", "sentence_transformers"
    ] = Field(default="openai")

    EMBEDDING_DIMENSION: int = Field(default=1536)

    # Provider API Keys
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    GOOGLE_API_KEY: Optional[str] = Field(default=None)
    GOOGLE_GEMINI_API_KEY: Optional[str] = Field(default=None)
    GROQ_API_KEY: Optional[str] = Field(default=None)
    OPENROUTER_API_KEY: Optional[str] = Field(default=None)
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")

    # RAG Settings
    RAG_CHUNK_SIZE: int = Field(default=500)
    RAG_CHUNK_OVERLAP: int = Field(default=50)
    RAG_TOP_K: int = Field(default=5)

    # Security & Limits
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    MAX_TOKENS_PER_SESSION: int = Field(default=50000)
    MAX_CONVERSATION_HISTORY: int = Field(default=20)
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(f"Invalid CORS origins configuration: {v}")


# Cached settings instance
settings = Settings()
