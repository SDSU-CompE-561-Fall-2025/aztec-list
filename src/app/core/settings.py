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
        ...,
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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",  # allows APP__TITLE style vars
        case_sensitive=False,
        extra="ignore",  # ignore extra fields from .env
    )

    app: AppMeta = Field(default_factory=AppMeta)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    a2: Argon2Settings


def load_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = load_settings()
