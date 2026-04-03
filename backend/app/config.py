from __future__ import annotations

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database - hostname 'fitness-db' avoids collision with other 'db' containers on Coolify network
    database_url: str = "postgresql+asyncpg://fitness@fitness-db:5432/fitness_rewards"

    # Auth
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # Strava
    strava_client_id: str = ""
    strava_client_secret: str = ""

    # Polar
    polar_client_id: str = ""
    polar_client_secret: str = ""

    # Groq (program extraction)
    groq_api_key: str = ""

    # App
    base_url: str = "https://fitness.littlefake.com"
    timezone: str = "Asia/Bangkok"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Module-level shortcut used by services
settings = get_settings()
