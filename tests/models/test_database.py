"""Unit tests for :mod:`pandaledger.models.database`."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from pandaledger.models.database import create_session_factory, create_sqlite_engine, init_db
from pandaledger.models.schema import Base


def test_create_sqlite_engine_creates_parent_directories(tmp_path: Path) -> None:
    """The database file's parent directory is created if missing."""
    db_path = tmp_path / "nested" / "data" / "pandaledger.sqlite3"

    engine = create_sqlite_engine(db_path)
    init_db(engine)

    assert db_path.parent.is_dir()


def test_init_db_creates_every_declared_table(tmp_path: Path) -> None:
    """init_db() creates a table for every mapped model."""
    engine = create_sqlite_engine(tmp_path / "pandaledger.sqlite3")

    init_db(engine)

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    assert existing_tables == set(Base.metadata.tables.keys())


def test_foreign_keys_are_enforced(tmp_path: Path) -> None:
    """SQLite's default (off) FK enforcement is turned on for every connection."""
    engine = create_sqlite_engine(tmp_path / "pandaledger.sqlite3")
    init_db(engine)

    with engine.connect() as connection:
        result = connection.execute(text("PRAGMA foreign_keys")).scalar()

    assert result == 1


def test_create_session_factory_produces_working_sessions(tmp_path: Path) -> None:
    """Sessions from the factory can round-trip a row through the real engine."""
    engine = create_sqlite_engine(tmp_path / "pandaledger.sqlite3")
    init_db(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        assert isinstance(session, Session)
        session.execute(text("SELECT 1"))
