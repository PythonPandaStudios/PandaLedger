"""Unit tests for the persistent left-nav application shell (PRD §7.1)."""

from __future__ import annotations

import pytest
import toga

from pandaledger.app import PandaLedgerApp, main
from pandaledger.views.main_window import NAV_ITEMS, MainWindow


@pytest.fixture
def started_app() -> PandaLedgerApp:
    """A ``PandaLedgerApp`` that has completed ``startup()`` on the dummy backend."""
    app = main()
    app._startup()
    return app


def test_startup_builds_a_main_window(started_app: PandaLedgerApp) -> None:
    """Starting the app produces a ``MainWindow`` instance titled after the app."""
    assert isinstance(started_app.shell, MainWindow)
    assert started_app.main_window is started_app.shell
    assert started_app.shell.title == started_app.formal_name


def test_nav_items_cover_every_prd_section() -> None:
    """The nav lists exactly the seven §7.1 sections, in the specified order."""
    labels = [label for label, _ in NAV_ITEMS]
    assert labels == [
        "Dashboard",
        "Transactions",
        "Budget",
        "Savings",
        "Paycheck",
        "Import",
        "Settings",
    ]


def test_dashboard_is_selected_on_startup(started_app: PandaLedgerApp) -> None:
    """The content pane shows Dashboard content immediately after startup."""
    main_window = started_app.shell
    assert main_window._active_label == "Dashboard"
    assert len(main_window._content_pane.children) == 1


def test_selecting_a_nav_item_swaps_the_content_pane(started_app: PandaLedgerApp) -> None:
    """Selecting a different section replaces the content pane's single child."""
    main_window = started_app.shell

    main_window._select("Paycheck")

    assert main_window._active_label == "Paycheck"
    assert len(main_window._content_pane.children) == 1
    heading = main_window._content_pane.children[0].children[0]
    assert isinstance(heading, toga.Label)
    assert heading.text == "Paycheck"


def test_reselecting_the_active_item_is_a_no_op(started_app: PandaLedgerApp) -> None:
    """Clicking the already-active nav item doesn't rebuild the content pane."""
    main_window = started_app.shell
    main_window._select("Budget")
    current_child = main_window._content_pane.children[0]

    main_window._select("Budget")

    assert main_window._content_pane.children[0] is current_child
