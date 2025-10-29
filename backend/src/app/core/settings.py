from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppMeta(BaseModel):
    title: str = "Aztec List"
    description: str = "API for an OfferUp-style marketplace for college students"
    version: str = "0.1.0"
    docs_url: str | None = "/docs"
    redoc_url: str | None = "/redoc"


class Argon2Settings(BaseModel):
    secret_key: str = Field(
        # TODO: Come up with warning later for not changing key
        default="CHANGE_ME_generate_a_secure_random_key_here",
        min_length=32,
        description="The secret key for JWT (configure via environment variable)",
    )
    algorithm: str = Field(
        default="HS256",
        description="The algorithm used for JWT",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        description="Access token expiration time in minutes",
    )


class DatabaseSettings(BaseModel):
    database_url: str = Field(
        default="sqlite:///./aztec_list.db",
        description="Database connection URL (PostgreSQL, SQLite, etc.)",
    )
    echo: bool = Field(
        default=False,
        description="Echo SQL statements to console (useful for debugging)",
    )


class ModerationSettings(BaseModel):
    strike_auto_ban_threshold: int = Field(
        default=3,
        ge=1,
        description="Number of strikes before automatic permanent ban",
    )


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Settings can be configured via:
    - .env file (loaded automatically from project root)
    - Environment variables with nested structure using __ delimiter
    """

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",  # allows APP__TITLE style vars
        case_sensitive=False,
        extra="ignore",  # ignore extra fields from .env
    )

    app: AppMeta = Field(default_factory=AppMeta)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    a2: Argon2Settings = Field(default_factory=Argon2Settings)
    moderation: ModerationSettings = Field(default_factory=ModerationSettings)


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are loaded only once.
    This is the recommended pattern for FastAPI dependency injection.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()
