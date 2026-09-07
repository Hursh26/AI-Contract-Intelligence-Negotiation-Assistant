"""Shared pytest fixtures.

Tests run against a temporary on-disk SQLite database and a temp storage
directory — never the real Postgres connection or production storage path
— so the whole suite has zero external infra requirements and runs
identically on macOS, Linux, and Windows CI runners (see .github/workflows/ci.yml).
"""

from collections.abc import Generator, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401  (registers all models on Base.metadata)
import app.utils.storage as storage_module
from app.api.deps import get_db
from app.db.base import Base
from app.main import app


@pytest.fixture()
def db_session(tmp_path: Path) -> Iterator[Session]:
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(
    db_session: Session, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[TestClient]:
    def _get_db_override() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    monkeypatch.setattr(storage_module, "STORAGE_ROOT", tmp_path / "storage")

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
