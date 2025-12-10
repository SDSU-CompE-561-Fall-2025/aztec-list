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


class JWTSettings(BaseModel):
    secret_key: str = Field(
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


class ListingSettings(BaseModel):
    max_images_per_listing: int = Field(
        default=10,
        ge=1,
        description="Maximum number of images allowed per listing",
    )


class StorageSettings(BaseModel):
    """File storage configuration for uploaded images."""

    upload_dir: str = Field(
        default="uploads/images",
        description="Directory for storing uploaded images (relative to backend root)",
    )
    profile_upload_dir: str = Field(
        default="uploads/profiles",
        description="Directory for storing profile pictures (relative to backend root)",
    )
    max_file_size_mb: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum file size in megabytes for image uploads",
    )
    allowed_extensions: list[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".webp", ".gif"],
        description="Allowed file extensions for image uploads",
    )
    allowed_mime_types: list[str] = Field(
        default=["image/jpeg", "image/png", "image/webp", "image/gif"],
        description="Allowed MIME types for image uploads",
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


class EmailSettings(BaseModel):
    """Email service configuration using Resend."""

    resend_api_key: str = Field(
        default="",
        description="Resend API key (configure via RESEND_API_KEY environment variable)",
    )
    from_email: str = Field(
        default="support@yourdomain.com",
        description="From email address for outgoing emails",
    )
    support_email: str = Field(
        default="support@yourdomain.com",
        description="Email address where support tickets are sent",
    )
    enabled: bool = Field(
        default=True,
        description="Enable/disable email sending (useful for testing)",
    )


class RateLimitSettings(BaseModel):
    """Rate limiting configuration."""

    enabled: bool = Field(
        default=True,
        description="Master switch to enable/disable all rate limiting (useful for emergencies or testing)",
    )


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Settings can be configured via:
    - .env file (loaded automatically from backend/ directory)
    - Environment variables with nested structure using __ delimiter
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",  # allows APP__TITLE style vars
        case_sensitive=False,
        extra="ignore",  # ignore extra fields from .env
    )

    app: AppMeta = Field(default_factory=AppMeta)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    moderation: ModerationSettings = Field(default_factory=ModerationSettings)
    listing: ListingSettings = Field(default_factory=ListingSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    email: EmailSettings = Field(default_factory=EmailSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)


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
