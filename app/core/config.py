from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = "Betting Core API"
    env: str = os.getenv("ENV", "dev")
    db_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://betting:betting@127.0.0.1:5433/betting_core",
    )


settings = Settings()
