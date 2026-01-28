"""Application configuration using pydantic-settings."""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "Blog Agent API"
    app_version: str = "0.1.0"
    debug: bool = False

    # API
    api_v1_prefix: str = "/api/v1"

    # CORS - configurable via environment variables
    # CORS_ORIGINS: comma-separated list, e.g., "http://localhost:3000,https://app.example.com"
    # Use ["*"] only for development without credentials
    cors_origins: list[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    @model_validator(mode="after")
    def validate_cors_config(self) -> "Settings":
        """Ensure CORS config is valid: credentials require explicit origins."""
        if self.cors_allow_credentials and "*" in self.cors_origins:
            # When credentials are enabled, wildcard origin is not allowed
            # Disable credentials to allow wildcard origin
            self.cors_allow_credentials = False
        return self


settings = Settings()
