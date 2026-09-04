"""Unit tests for the persistent left-nav application shell (PRD §7.1)."""

from __future__ import annotations

import pytest
import toga
from travertino.colors import Color

from pandaledger.app import PandaLedgerApp, main
from pandaledger.views.main_window import NAV_ITEMS, MainWindow
from pandaledger.views.theme import DARK_PALETTE, LIGHT_PALETTE, ThemeMode

# Pack's background_color/color properties store a parsed `Color`, not the
# raw hex string that was assigned, so comparisons need both sides parsed.
_color = Color.parse


@pytest.fixture
def started_app() -> PandaLedgerApp:
    """A ``PandaLedgerApp`` on the dummy backend, past the first-run wizard.

    A fresh test database has no Account yet, so ``_startup()`` shows the
    first-run wizard rather than the main window (see
    ``tests/views/wizard/test_wizard_window.py`` for wizard-specific
    coverage). These tests are about the main window's own nav/theme
    behavior, so the fixture calls the same ``_show_main_window`` the
    wizard's "Finish" button would, to get there directly.
    """
    app = main()
    app._startup()
    app._show_main_window()
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


def test_starts_styled_with_the_light_palette(started_app: PandaLedgerApp) -> None:
    """Nav chrome is styled with the light palette by default."""
    main_window = started_app.shell

    assert main_window._nav_column.style.background_color == _color(LIGHT_PALETTE.surface)
    assert main_window._content_pane.style.background_color == _color(LIGHT_PALETTE.background)
    for button in main_window._nav_buttons.values():
        assert button.style.background_color == _color(LIGHT_PALETTE.surface)
        assert button.style.color == _color(LIGHT_PALETTE.text)


def test_toggling_theme_restyles_nav_chrome(started_app: PandaLedgerApp) -> None:
    """Switching to dark mode re-colors the nav column, buttons, and content pane."""
    main_window = started_app.shell

    started_app.theme.toggle()

    assert started_app.theme.mode is ThemeMode.DARK
    assert main_window._nav_column.style.background_color == _color(DARK_PALETTE.surface)
    assert main_window._content_pane.style.background_color == _color(DARK_PALETTE.background)
    for button in main_window._nav_buttons.values():
        assert button.style.background_color == _color(DARK_PALETTE.surface)
        assert button.style.color == _color(DARK_PALETTE.text)


def test_toggling_theme_rebuilds_the_active_section_in_place(started_app: PandaLedgerApp) -> None:
    """The currently visible section is rebuilt (same label) after a theme switch."""
    main_window = started_app.shell
    main_window._select("Paycheck")

    started_app.theme.toggle()

    assert main_window._active_label == "Paycheck"
    heading = main_window._content_pane.children[0].children[0]
    assert isinstance(heading, toga.Label)
    assert heading.text == "Paycheck"
