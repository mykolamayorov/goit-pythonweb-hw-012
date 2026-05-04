"""
Database setup.

This module initializes the SQLAlchemy engine and session factory, and provides
a FastAPI dependency for obtaining a DB session.

Design:
- Uses SQLAlchemy Engine (sync) with PostgreSQL driver psycopg2.
- Provides SessionLocal factory for request-scoped sessions.
- get_db() yields a session and guarantees it is closed afterwards.

Usage:
- Import Base in models module and declare models inheriting from Base.
- Use get_db dependency in API routes to interact with DB safely.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import DATABASE_URL


class Base(DeclarativeBase):
    """
    Declarative base class for SQLAlchemy models.
    """
    pass


# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency: provide a SQLAlchemy session.

    Yields a session for the duration of the request and closes it afterwards.

    :yield: SQLAlchemy Session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()