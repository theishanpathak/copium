"""Typed application settings, loaded from the environment or .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Copium backend."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    TAVILY_API_KEY: str


settings = Settings()