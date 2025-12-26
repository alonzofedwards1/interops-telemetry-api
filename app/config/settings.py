import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    port: int = int(os.environ.get("PORT", 8080))


def get_settings() -> Settings:
    return Settings()
