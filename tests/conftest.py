"""Pytest configuration shared across the whole test suite.

Forces Toga's dummy backend so UI tests run headlessly (no GTK display
required in CI or a dev container). This must be set before anything
imports ``toga``, so it lives at module scope in the top-level conftest,
which pytest loads before collecting any test module.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("TOGA_BACKEND", "toga_dummy")


@pytest.fixture(autouse=True)
def _isolate_home_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point ``$HOME`` at a per-test temp directory for every test.

    toga_dummy's ``Paths.get_data_path()`` resolves to ``Path.home() /
    "user_data" / app_id`` — any test that starts a ``PandaLedgerApp``
    (which creates its SQLite database under that path) would otherwise
    read and write a real file under the developer's actual home
    directory, making tests order-dependent on real, accumulating state
    (e.g. a leftover Account from a prior run silently skipping the
    first-run wizard in a later one) — a real bug caught by noticing that
    exact file appear during this suite's first run.
    """
    monkeypatch.setenv("HOME", str(tmp_path))
