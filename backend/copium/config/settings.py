"""Typed application settings, loaded from the environment or .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Copium backend."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    ROAST_MODEL: str = "gpt-4o"
    TAVILY_API_KEY: str
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_HOST: str = "https://us.cloud.langfuse.com"
    SUPABASE_URL: str
    SUPABASE_SECRET_KEY: str
    GCP_PROJECT_ID: str = "copium-504602"
    PUBSUB_TOPIC: str = "gmail-job-apps"
    JOB_APPS_LABEL_ID: str = "Label_2983195907014674210"

settings = Settings()