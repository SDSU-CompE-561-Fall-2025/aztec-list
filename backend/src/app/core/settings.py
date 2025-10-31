from functools import lru_cache

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.enums import LogLevel


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


class CORSSettings(BaseModel):
    """
    Cross-Origin Resource Sharing (CORS) configuration.

    Configure allowed origins, methods, and headers for cross-origin requests.

    SECURITY NOTE:
    - The default localhost origins are suitable for DEVELOPMENT ONLY
    - In PRODUCTION, override these with actual frontend domains
    - Never use wildcard "*" with allow_credentials=True (security risk)
    """

    allowed_origins: list[str] = Field(
        default=["http://localhost:3000"],
        min_length=1,
        description="List of allowed origins for CORS (frontend URLs). Override in production!",
    )
    allow_credentials: bool = Field(
        default=True,
        description="Allow cookies and authentication headers in CORS requests",
    )
    allowed_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        description="HTTP methods allowed for CORS requests",
    )
    allowed_headers: list[str] = Field(
        default=["*"],
        description="HTTP headers allowed in CORS requests (* allows all)",
    )

    @model_validator(mode="after")
    def validate_credentials_with_wildcard(self) -> "CORSSettings":
        """
        Prevent dangerous combination of wildcard origins with credentials.

        Security Issue: Using allow_credentials=True with allowed_origins=["*"]
        creates a security vulnerability where any website can make authenticated
        requests to your API.

        Raises:
            ValueError: If wildcard origin is used with credentials enabled
        """
        if self.allow_credentials and "*" in self.allowed_origins:
            msg = (
                "Security Error: Cannot use wildcard origin '*' with allow_credentials=True. "
                "This allows ANY website to make authenticated requests to your API. "
                "Either set allow_credentials=False or specify explicit origins."
            )
            raise ValueError(msg)

        return self


class LoggingSettings(BaseModel):
    """Application logging configuration."""

    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format string",
    )
    use_json: bool = Field(
        default=False,
        description="Use JSON formatting for logs (recommended for production)",
    )
    uvicorn_access_level: LogLevel = Field(
        default=LogLevel.WARNING,
        description="Logging level for Uvicorn access logs",
    )
    uvicorn_error_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level for Uvicorn error logs",
    )
    excluded_paths: list[str] = Field(
        default=["/health", "/docs", "/redoc", "/openapi.json"],
        description="Paths to exclude from detailed request logging",
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
    cors: CORSSettings = Field(default_factory=CORSSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)


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
