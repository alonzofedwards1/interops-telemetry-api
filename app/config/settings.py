import os
from dataclasses import dataclass
from typing import List, Optional


DEFAULT_PORT = 8000
# Default API prefix matches the frontend client's base path so requests hit the
# expected routes without extra configuration.
DEFAULT_API_PREFIX = "/api"


@dataclass(frozen=True)
class Settings:
    """Application settings."""

    # Use a dedicated env var to override only when intentional; default to 8000.
    port: int = int(os.environ.get("TELEMETRY_PORT", DEFAULT_PORT))
    allowed_origins: List[str] = None
    api_prefix: str = DEFAULT_API_PREFIX


def get_settings() -> Settings:
    origins_value = os.environ.get("CORS_ORIGINS", "*")
    origins = [origin.strip() for origin in origins_value.split(",") if origin.strip()] or ["*"]
    prefix_value = os.environ.get("API_PREFIX", DEFAULT_API_PREFIX)
    if prefix_value and not prefix_value.startswith("/"):
        prefix_value = f"/{prefix_value}"

    return Settings(allowed_origins=origins, api_prefix=prefix_value)
