import os
import sys
import uuid

import pytest
import psycopg2
import redis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ✅ Ensure project root is on PYTHONPATH so "import app" works in container
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.config import REDIS_URL  # noqa: E402


# We'll use a dedicated test database inside the same Postgres server.
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "postgres_test")

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mysecretpassword")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")

ADMIN_DSN = f"dbname=postgres user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"
TEST_DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}"


def _ensure_test_database() -> None:
    """Create test database if it doesn't exist."""
    conn = psycopg2.connect(ADMIN_DSN)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (TEST_DB_NAME,))
            exists = cur.fetchone() is not None
            if not exists:
                cur.execute(f"CREATE DATABASE {TEST_DB_NAME}")
    finally:
        conn.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Create a dedicated test database and initialize schema once per test session.
    We create/drop tables to start with a clean schema.
    """
    _ensure_test_database()

    from app.database import Base
    import app.models  # noqa: F401

    engine = create_engine(TEST_DATABASE_URL, echo=False)

    # Start clean
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    # Optional cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="session")
def engine():
    """SQLAlchemy engine bound to the test database."""
    return create_engine(TEST_DATABASE_URL, echo=False)


@pytest.fixture()
def db_session(engine):
    """
    Create a DB session wrapped in a transaction and rollback after each test.
    This keeps tests isolated and fast.
    """
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(autouse=True)
def patch_email_sending(monkeypatch):
    """
    Disable real SMTP for tests.
    We don't want tests to send emails to Mailtrap.
    """
    import app.services.email as email_service

    monkeypatch.setattr(email_service, "send_verification_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(email_service, "send_password_reset_email", lambda *args, **kwargs: None)


@pytest.fixture(autouse=True)
def flush_redis():
    """Flush Redis between tests to make caching deterministic."""
    try:
        r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        r.flushdb()
    except Exception:
        # If Redis is not reachable, tests can still run for non-cache flows
        pass


@pytest.fixture()
def client(db_session):
    """
    Provide FastAPI TestClient with DB dependency overridden to use test DB session.
    """
    from app.main import app
    from app.database import get_db

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def _rand_email(prefix: str = "user") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture()
def random_email():
    """Provide a random unique email for tests."""
    return _rand_email()