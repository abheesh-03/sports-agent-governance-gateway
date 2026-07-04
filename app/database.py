"""Database setup for the gateway.

Uses SQLAlchemy with SQLite by default. The engine, session factory, and
declarative base are defined here. Tables are created via ``init_db`` which is
invoked on application startup.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# SQLite requires ``check_same_thread=False`` so the connection can be shared
# across FastAPI's threadpool. For other databases this argument is omitted.
connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db() -> None:
    """Create all tables. Safe to call multiple times."""
    # Import models so they are registered on the metadata before create_all.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency that yields a database session and closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
