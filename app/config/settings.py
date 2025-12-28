import os
from dataclasses import dataclass
from typing import List, Optional


DEFAULT_PORT = 8081


@dataclass(frozen=True)
class Settings:
    """Application settings."""

    # Use a dedicated env var to override only when intentional; default to 8081.
    port: int = int(os.environ.get("TELEMETRY_PORT", DEFAULT_PORT))
    allowed_origins: List[str] = None
    mirth_pd_endpoint_url: Optional[str] = os.environ.get("MIRTH_PD_ENDPOINT_URL")
    openemr_client_id: Optional[str] = os.environ.get("OPENEMR_CLIENT_ID")
    openemr_client_secret: Optional[str] = os.environ.get("OPENEMR_CLIENT_SECRET")
    openemr_token_url: Optional[str] = os.environ.get("OPENEMR_TOKEN_URL")
    openemr_username: Optional[str] = os.environ.get("OPENEMR_USERNAME")
    openemr_password: Optional[str] = os.environ.get("OPENEMR_PASSWORD")
    openemr_scope: Optional[str] = os.environ.get("OPENEMR_SCOPE")


def get_settings() -> Settings:
    origins_value = os.environ.get("CORS_ORIGINS", "*")
    origins = [origin.strip() for origin in origins_value.split(",") if origin.strip()] or ["*"]
    return Settings(allowed_origins=origins)
