"""Core configuration module."""
from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None
    storage_bucket: str = "client-documents"
    storage_public: bool = False  # If True, bucket is public; if False, use signed URLs

    # WhatsApp (optional based on WHATSAPP_ENABLED)
    whatsapp_enabled: bool = True  # Set to false to test without WhatsApp
    whatsapp_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_business_account_id: Optional[str] = None
    whatsapp_app_secret: Optional[str] = None  # For webhook signature verification
    verify_token: Optional[str] = None

    # Dev Mode (for testing without WhatsApp)
    dev_endpoints_enabled: bool = False  # Enable /dev endpoints for testing
    dev_token: str = "dev-secret-change-me"  # Token to protect /dev endpoints

    # Application
    app_base_url: str = "http://localhost:8000"
    environment: str = "development"
    log_level: str = "INFO"

    # API
    api_v1_prefix: str = "/api/v1"
    
    # Pagination
    default_page_size: int = 50
    max_page_size: int = 100

    # Media download
    media_download_timeout: int = 30
    media_download_retries: int = 3

    # Mock Mode Configuration
    app_mode: str = "real"  # "mock" or "real"
    mock_seed_on_start: bool = False
    mock_dataset_name: str = "default"
    storage_mode: str = "supabase"  # "local" or "supabase"
    db_mode: str = "supabase"  # "sqlite", "postgres", or "supabase"

    @field_validator("*", mode="after")
    @classmethod
    def validate_required_fields(cls, v, info):
        """Validate required fields based on mode configurations."""
        # Skip validation during creation, will validate in __init__
        return v

    def __init__(self, **data):
        """Initialize settings with conditional validation."""
        super().__init__(**data)
        self._validate_mode_requirements()

    def _validate_mode_requirements(self):
        """Validate that required env vars are present based on mode."""
        missing = []

        # Real mode requires Supabase configuration
        if self.app_mode == "real":
            if not self.supabase_url:
                missing.append("SUPABASE_URL")
            if not self.supabase_service_role_key:
                missing.append("SUPABASE_SERVICE_ROLE_KEY")

        # WhatsApp enabled requires WhatsApp configuration
        if self.whatsapp_enabled and self.app_mode == "real":
            if not self.whatsapp_token:
                missing.append("WHATSAPP_ACCESS_TOKEN (or set WHATSAPP_ENABLED=false)")
            if not self.whatsapp_phone_number_id:
                missing.append("WHATSAPP_PHONE_NUMBER_ID (or set WHATSAPP_ENABLED=false)")
            if not self.verify_token:
                missing.append("WHATSAPP_VERIFY_TOKEN (or set WHATSAPP_ENABLED=false)")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Current mode: APP_MODE={self.app_mode}, WHATSAPP_ENABLED={self.whatsapp_enabled}\n"
                f"Set these in your .env file or adjust mode flags."
            )

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra env vars like DATABASE_URL (used by Prisma)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
