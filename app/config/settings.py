import os
from dataclasses import dataclass
from typing import List


DEFAULT_PORT = 9000


@dataclass(frozen=True)
class Settings:
    """Application settings."""

    # Use a dedicated env var to override only when intentional; default to 9000.
    port: int = int(os.environ.get("TELEMETRY_PORT", DEFAULT_PORT))
    allowed_origins: List[str] = None


def get_settings() -> Settings:
    origins_value = os.environ.get("CORS_ORIGINS", "*")
    origins = [origin.strip() for origin in origins_value.split(",") if origin.strip()] or ["*"]
    return Settings(allowed_origins=origins)
