"""Small shared UI helpers used across multiple screens in :mod:`pandaledger.views`."""

from __future__ import annotations

import toga
from toga.style import Pack
from travertino.constants import COLUMN

from pandaledger.views.theme import Palette

#: Padding applied around the content of every top-level nav section, so
#: screens have consistent breathing room without each one repeating it.
SECTION_PADDING = 16


def section_box(title: str, empty_state_message: str, palette: Palette) -> toga.Box:
    """Build a top-level section's root box with a heading and empty-state copy.

    Every nav destination starts life as a heading plus an explanatory
    message describing what will appear once there is data to show (e.g.
    accounts, transactions). This keeps each screen a complete, real widget
    tree — never a stub — while its backing controller/model work is built
    out feature-by-feature.

    Args:
        title: The section heading shown at the top of the screen.
        empty_state_message: Copy explaining what the user should do, or
            what will appear here, before this section has real data.
        palette: The active color palette (PRD §7.1 light/dark theme) to
            style the heading, message, and background with.

    Returns:
        A vertical ``toga.Box`` containing the heading and message, ready
        to be used as a nav section's content or extended with more
        children by the caller.
    """
    heading = toga.Label(
        title,
        style=Pack(font_size=20, font_weight="bold", color=palette.text, margin_bottom=8),
    )
    message = toga.Label(
        empty_state_message,
        style=Pack(color=palette.text_muted, margin_bottom=4),
    )
    return toga.Box(
        children=[heading, message],
        style=Pack(
            direction=COLUMN,
            background_color=palette.background,
            margin=SECTION_PADDING,
            flex=1,
        ),
    )
