from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    API_KEYS: str = "writer1=read,odds:write,predictions:write,bets:write;reader1=read"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    RATE_LIMIT_ENABLED: bool = False
    RL_ODDS_PER_KEY_CAP: int = 20
    RL_ODDS_PER_KEY_REFILL: float = 20.0
    RL_ODDS_GLOBAL_CAP: int = 100
    RL_ODDS_GLOBAL_REFILL: float = 100.0

settings = Settings()