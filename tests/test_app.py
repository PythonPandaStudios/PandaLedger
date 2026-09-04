"""Unit tests for the top-level application entry point."""

from __future__ import annotations

from pandaledger.app import PandaLedgerApp, main


def test_main_returns_configured_app() -> None:
    """``main()`` builds an app with the expected identity, not yet started."""
    app = main()

    assert isinstance(app, PandaLedgerApp)
    assert app.formal_name == "PandaLedger"
    assert app.app_id == "studios.pythonpanda.pandaledger"


def test_startup_sets_main_window() -> None:
    """Calling startup() (as Toga does on launch) attaches a main window."""
    app = main()

    app._startup()

    assert app.main_window is not None
