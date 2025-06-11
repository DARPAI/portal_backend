from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from .types import Environment
from .types import LLMModel


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_ignore_empty=True)

    LOG_DIR: Path = Path("logs")
    ENVIRONMENT: Environment = Environment.deployed
    PROXY: str | None = None
    API_PORT: int
    REGISTRY_URL: str = "http://registry:80"

    PG_USER: str
    PG_PASSWORD: str
    PG_DB: str = "portal_backend"
    PG_HOST: str = "portal_postgres"
    PG_PORT: int = 5432

    DB_POOL_SIZE: int = 50
    DB_MAX_OVERFLOW: int = 25
    LOG_LEVEL: str = "INFO"

    DEFAULT_LLM_MODEL: LLMModel = "anthropic/claude-3.7-sonnet"
    DEFAULT_AVATAR_URL: str = (
        "https://toci-s3-bucket-aws-02.s3.eu-central-1.amazonaws.com/8883fe75-ce0f-4546-9fbb-65d75d45568a.png"
    )
    DEFAULT_AGENT_SERVER_IDS: list[int] = []
    DEFAULT_AGENT_NAME: str = "Default"
    DEFAULT_AGENT_DESCRIPTION: str = "Default agent"

    OPENROUTER_API_KEY: str

    S3_ACCESS: str
    S3_SECRET: str
    S3_BUCKET: str
    S3_HOST: str
    CDN_BASE_URL: str


settings = Settings()
