import os
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Settings:
    port: int = int(os.environ.get("PORT", 8080))
    allowed_origins: List[str] = None


def get_settings() -> Settings:
    origins_value = os.environ.get("CORS_ORIGINS", "*")
    origins = [origin.strip() for origin in origins_value.split(",") if origin.strip()] or ["*"]
    return Settings(allowed_origins=origins)
