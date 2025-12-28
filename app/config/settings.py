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
    api_prefix: str = "/api"


def get_settings() -> Settings:
    origins_value = os.environ.get("CORS_ORIGINS", "*")
    origins = [origin.strip() for origin in origins_value.split(",") if origin.strip()] or ["*"]
    prefix_value = os.environ.get("API_PREFIX", "/api")
    prefix = prefix_value if prefix_value.startswith("/") else f"/{prefix_value}"

    return Settings(allowed_origins=origins, api_prefix=prefix)
