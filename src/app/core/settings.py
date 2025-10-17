from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppMeta(BaseModel):
    title: str = "Aztec List"
    description: str = "API for an OfferUp-style marketplace for college students"
    version: str = "0.1.0"
    docs_url: str | None = "/docs"
    redoc_url: str | None = "/redoc"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",  # allows APP__TITLE style vars
        case_sensitive=False,
    )

    app: AppMeta = AppMeta()


settings = Settings()
