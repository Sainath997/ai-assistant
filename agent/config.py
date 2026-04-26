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
    api_token: str = Field("", env="API_TOKEN")
    allowed_origins: str = Field("*", env="ALLOWED_ORIGINS")
    rate_limit_per_minute: int = Field(60, env="RATE_LIMIT_PER_MINUTE")

    # Memory
    chroma_persist_dir: str = Field("./memory/chroma_db", env="CHROMA_PERSIST_DIR")
    sqlite_db_path: str = Field("./memory/assistant.db", env="SQLITE_DB_PATH")
    filesystem_root: str = Field(".", env="FILESYSTEM_ROOT")

    # Calendar (CalDAV / Google-compatible providers)
    caldav_url: str = Field("", env="CALDAV_URL")
    caldav_username: str = Field("", env="CALDAV_USERNAME")
    caldav_password: str = Field("", env="CALDAV_PASSWORD")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
