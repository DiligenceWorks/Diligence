from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


def _default_data_dir() -> Path:
    """~/.diligence on all platforms."""
    d = Path.home() / ".diligence"
    d.mkdir(exist_ok=True)
    return d


class Settings(BaseSettings):
    # Database — empty string triggers SQLite auto-detect (pip install path)
    # Set DATABASE_URL explicitly for PostgreSQL (Docker path)
    database_url: str = ""

    # Auth
    secret_key: str = "change-me-in-production"
    crawl_enabled: bool = False
    access_token_expire_minutes: int = 1440  # 24 hours
    api_token: str = ""  # MCP connector auth

    # Strava
    strava_client_id: str = ""
    strava_client_secret: str = ""

    # Polar
    polar_client_id: str = ""
    polar_client_secret: str = ""

    # Groq (program extraction)
    groq_api_key: str = ""

    # Telegram (support notifications)
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # App
    base_url: str = "http://localhost:8000"
    timezone: str = "Asia/Bangkok"
    data_dir: str = str(_default_data_dir())

    # MCP
    mcp_enabled: bool = True
    mcp_port: int = 3001

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def effective_database_url(self) -> str:
        """Return the database URL, falling back to SQLite if not set."""
        if self.database_url:
            return self.database_url
        db_path = Path(self.data_dir) / "data.db"
        return f"sqlite+aiosqlite:///{db_path}"

    @property
    def is_sqlite(self) -> bool:
        return self.effective_database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Module-level shortcut used by services
settings = get_settings()
