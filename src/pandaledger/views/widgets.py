"""Small shared UI helpers used across multiple screens in :mod:`pandaledger.views`."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

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


def labeled_field(label_text: str, widget: toga.Widget, palette: Palette) -> toga.Box:
    """Stack a caption label above a form input, for consistent form layout.

    Args:
        label_text: Caption shown above ``widget``.
        widget: The input widget the caption describes.
        palette: Active color palette; the caption uses ``palette.text_muted``.

    Returns:
        A vertical ``toga.Box`` containing the caption and the widget.
    """
    caption = toga.Label(label_text, style=Pack(color=palette.text_muted, margin_bottom=2))
    return toga.Box(children=[caption, widget], style=Pack(direction=COLUMN, margin_bottom=10))


def selected_label(selection: toga.Selection) -> str:
    """Read a ``Selection`` widget's current value as a ``str``.

    ``Selection.value`` is typed ``object`` upstream, since Toga supports
    arbitrary list-source items with an accessor — but every ``Selection``
    in this app is built from a plain list of label strings, so its value
    is always a ``str`` at runtime. This narrows that for callers that
    look the label up in a ``dict[str, ...]`` (mypy --strict rejects
    indexing a ``dict[str, X]`` with an ``object`` key).

    Args:
        selection: A ``Selection`` widget built from ``items=[...]`` of
            plain strings.

    Returns:
        The currently selected label.

    Raises:
        AssertionError: If the selection's value isn't a ``str`` — which
            would mean it was built with non-string items, a programming
            error in the caller.
    """
    value = selection.value
    assert isinstance(value, str), f"expected a str Selection value, got {type(value)!r}"
    return value


def parse_dollars_to_cents(text: str) -> int:
    """Parse a user-typed dollar amount into integer cents.

    Uses :class:`decimal.Decimal` rather than ``float`` for the conversion,
    so a value like "19.99" can't pick up floating-point rounding error on
    its way to cents — PRD §6's "money is never a float" rule applies in
    transit from user input too, not just in storage.

    Args:
        text: The typed amount, e.g. ``"1234.56"``, ``"-42"``, or ``"42.5"``.

    Returns:
        The amount in integer cents.

    Raises:
        ValueError: If ``text`` isn't a valid decimal number.
    """
    try:
        dollars = Decimal(text.strip())
    except InvalidOperation as error:
        raise ValueError(f"{text!r} is not a valid dollar amount") from error
    return int((dollars * 100).to_integral_value())
