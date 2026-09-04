"""Settings screen (PRD §7.1, §7.8).

Currently holds the Appearance section (light/dark theme toggle, PRD §7.1).
Budget/savings strategy changes and tax table management will live here
too, once their controllers/models exist.
"""

from __future__ import annotations

import toga
from toga.style import Pack
from travertino.constants import COLUMN

from pandaledger.views.theme import ThemeManager, ThemeMode
from pandaledger.views.widgets import SECTION_PADDING, section_box


def build_settings_view(theme: ThemeManager) -> toga.Box:
    """Build the Settings nav section's root widget.

    Args:
        theme: The app's theme manager. The Appearance section reads its
            current mode for display and calls :meth:`ThemeManager.toggle`
            when the user presses the switch button.

    Returns:
        A ``toga.Box`` containing the Settings screen's content: a
        placeholder empty-state for not-yet-built sections, plus a working
        Appearance section.
    """
    root = section_box(
        title="Settings",
        empty_state_message=("Budget/savings strategy and tax table management will live here."),
        palette=theme.palette,
    )
    root.add(_build_appearance_section(theme))
    return root


def _build_appearance_section(theme: ThemeManager) -> toga.Box:
    """Build the Appearance sub-section: current mode + a toggle button.

    Args:
        theme: The app's theme manager.

    Returns:
        A vertical ``toga.Box`` with an "Appearance" heading, a label
        stating the active mode, and a button that switches it.
    """
    palette = theme.palette
    mode_label = "Light" if theme.mode is ThemeMode.LIGHT else "Dark"
    switch_to_label = "Dark" if theme.mode is ThemeMode.LIGHT else "Light"

    heading = toga.Label(
        "Appearance",
        style=Pack(font_size=16, font_weight="bold", color=palette.text, margin_bottom=4),
    )
    current_mode = toga.Label(
        f"Theme: {mode_label}",
        style=Pack(color=palette.text_muted, margin_bottom=8),
    )
    toggle_button = toga.Button(
        f"Switch to {switch_to_label}",
        on_press=lambda widget: theme.toggle(),
        style=Pack(width=180),
    )
    return toga.Box(
        children=[heading, current_mode, toggle_button],
        style=Pack(direction=COLUMN, margin_top=SECTION_PADDING),
    )
