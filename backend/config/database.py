from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from config.config import settings
import os

# Database URL (loaded from .env via config.settings)
DATABASE_URL = settings.database_url

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    poolclass=StaticPool if "sqlite" in DATABASE_URL else None,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """Create all tables in database"""
    from models.base import Base
    Base.metadata.create_all(bind=engine)


def drop_all_tables():
    """Drop all tables from database (use with caution)"""
    from models.base import Base
    Base.metadata.drop_all(bind=engine)
