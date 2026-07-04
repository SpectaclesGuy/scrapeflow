from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    app_name: str = Field(default='ScrapeFlow Scraper Service', alias='APP_NAME')
    env: str = Field(default='development', alias='ENV')
    database_url: str = Field(
        default='postgresql+psycopg2://postgres:postgres@localhost:5432/scrapeflow_context',
        alias='DATABASE_URL',
    )
    redis_url: str = Field(default='redis://localhost:6379/0', alias='REDIS_URL')
    output_dir: str = Field(default='outputs', alias='OUTPUT_DIR')
    default_headless: bool = Field(default=True, alias='DEFAULT_HEADLESS')
    default_timeout: int = Field(default=30000, alias='DEFAULT_TIMEOUT')
    max_pages_default: int = Field(default=5, alias='MAX_PAGES_DEFAULT')
    slm_enabled: bool = Field(default=True, alias='SLM_ENABLED')
    slm_provider: str = Field(default='gemini', alias='SLM_PROVIDER')
    slm_model: str = Field(default='gemini-3.5-flash', alias='SLM_MODEL')
    slm_api_url: str | None = Field(default=None, alias='SLM_API_URL')
    slm_api_key: str | None = Field(default=None, alias='SLM_API_KEY')
    slm_timeout: int = Field(default=30, alias='SLM_TIMEOUT')
    slm_max_input_chars: int = Field(default=12000, alias='SLM_MAX_INPUT_CHARS')
    gemini_api_key: str | None = Field(default=None, alias='GEMINI_API_KEY')
    gemini_base_url: str = Field(
        default='https://generativelanguage.googleapis.com/v1beta/openai',
        alias='GEMINI_BASE_URL',
    )
    session_secret: str = Field(default='dev-session-secret-change-me', alias='SESSION_SECRET')
    session_cookie_name: str = Field(default='scrapeflow_session', alias='SESSION_COOKIE_NAME')
    session_max_age: int = Field(default=604800, alias='SESSION_MAX_AGE')
    session_https_only: bool = Field(default=False, alias='SESSION_HTTPS_ONLY')
    google_client_id: str | None = Field(default=None, alias='GOOGLE_CLIENT_ID')
    google_client_secret: str | None = Field(default=None, alias='GOOGLE_CLIENT_SECRET')
    run_startup_migrations: bool = Field(default=False, alias='RUN_STARTUP_MIGRATIONS')

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        populate_by_name=True,
    )

    @property
    def output_path(self) -> Path:
        return Path(self.output_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()
