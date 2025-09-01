from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from functools import lru_cache
from typing import Dict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    API_KEYS: str = "writer1=read,odds:write,predictions:write,bets:write;reader1=read"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    RATE_LIMIT_ENABLED: bool = False
    RL_ODDS_PER_KEY_CAP: int = 20
    RL_ODDS_PER_KEY_REFILL: float = 20.0
    RL_ODDS_GLOBAL_CAP: int = 100
    RL_ODDS_GLOBAL_REFILL: float = 100.0

    AUTH_MODE: str = "both"  # "keys" | "jwt" | "both"

    # JWT-basics
    JWT_ALG: str = "HS256"
    JWT_ISSUER: str | None = "betting-core"
    JWT_AUDIENCE: str | None = "betting-clients"
    JWT_LEEWAY: int = 30

    # Rotation via KID "v1:secret1,v2:secret2"
    JWT_SECRETS: str = ""
    # Vilka KID som är accepterande just nu (t.ex under rotation): "v1, v2"
    JWT_ACCEPTED_KIDS: str = ""

    @property
    @lru_cache(maxsize=1)
    def jwt_keyset(self) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for part in (self.JWT_SECRETS or "").split(","):
            part = part.strip()
            if not part:
                continue
            if ":" not in part:
                continue
            kid, secret = part.split(":", 1)
            out[kid.strip()] = secret.strip()
        return out


settings = Settings()
