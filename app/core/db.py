from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(
    settings.db_url, 
    pool_size=30,
    max_overflow=60,
    pool_pre_ping=True,
    pool_recycle=1800,
    future=True
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ping_db():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        