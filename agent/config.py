"""Central configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # LLM
    llm_provider: str = Field("openai", env="LLM_PROVIDER")
    llm_model: str = Field("gpt-4o", env="LLM_MODEL")
    openai_api_key: str = Field("", env="OPENAI_API_KEY")
    anthropic_api_key: str = Field("", env="ANTHROPIC_API_KEY")
    ollama_base_url: str = Field("http://localhost:11434", env="OLLAMA_BASE_URL")

    # App
    app_host: str = Field("0.0.0.0", env="APP_HOST")
    app_port: int = Field(8000, env="APP_PORT")
    secret_key: str = Field("change-me", env="SECRET_KEY")

    # Memory
    chroma_persist_dir: str = Field("./memory/chroma_db", env="CHROMA_PERSIST_DIR")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
