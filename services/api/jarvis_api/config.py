from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="JARVIS_",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    env: str = "development"
    database_path: Path = Path("data/jarvis.db")
    default_provider: str = "auto"
    confirm_critical_actions: bool = True
    allowed_origins: str = "http://localhost:5173,http://localhost:4173,tauri://localhost"

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    xai_api_key: str | None = Field(default=None, validation_alias="XAI_API_KEY")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
