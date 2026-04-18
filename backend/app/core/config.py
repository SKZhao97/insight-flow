from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg:///insight_flow"
    report_export_dir: str = "runtime_exports/reports"
    fetch_user_agent: str = "InsightFlowBot/0.1"
    fetch_timeout_seconds: float = 20.0
    jina_reader_base_url: str | None = None
    firecrawl_base_url: str | None = None
    firecrawl_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
