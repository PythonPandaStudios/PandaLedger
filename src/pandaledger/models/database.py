"""SQLAlchemy engine/session setup (PRD §6, §8).

Toga-free per project rules: the platform-appropriate app-data directory
is resolved by the caller (``app.py``, which can import Toga) and handed
to this module as a plain ``pathlib.Path``, so this module stays headless
and testable on its own.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from pandaledger.models.schema import Base


def create_sqlite_engine(db_path: Path) -> Engine:
    """Create a SQLAlchemy engine for the app's SQLite database file.

    Args:
        db_path: Filesystem path to the SQLite database file. Its parent
            directory is created if it doesn't already exist.

    Returns:
        A configured SQLAlchemy ``Engine``, with SQLite foreign-key
        enforcement turned on for every connection it opens.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")

    # SQLite ignores foreign key constraints unless a connection explicitly
    # asks for them, per connection — without this, orphaned rows (e.g. a
    # Transaction pointing at a deleted Account) would fail silently rather
    # than raising, which is exactly the kind of quiet data corruption a
    # money app can't afford.
    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection: Any, connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def init_db(engine: Engine) -> None:
    """Create every table declared in :mod:`pandaledger.models.schema` that doesn't exist yet.

    Args:
        engine: The engine to create tables on.
    """
    Base.metadata.create_all(engine)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Build a session factory bound to ``engine``.

    Args:
        engine: The engine every session from this factory should use.

    Returns:
        A ``sessionmaker`` that produces new ``Session`` instances.
    """
    return sessionmaker(bind=engine)
