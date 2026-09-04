"""Unit tests for the Settings screen's Appearance (light/dark theme) section."""

from __future__ import annotations

import toga

from pandaledger.views.settings import build_settings_view
from pandaledger.views.theme import ThemeManager, ThemeMode


def _find_button(box: toga.Box, text: str) -> toga.Button:
    """Recursively find a Button with the given text within ``box``.

    Args:
        box: The box (and its descendants) to search.
        text: The exact button label to look for.

    Returns:
        The matching ``toga.Button``.

    Raises:
        AssertionError: If no matching button is found.
    """
    for child in box.children:
        if isinstance(child, toga.Button) and child.text == text:
            return child
        if isinstance(child, toga.Box):
            try:
                return _find_button(child, text)
            except AssertionError:
                continue
    raise AssertionError(f"No button with text {text!r} found")


def test_shows_the_current_mode() -> None:
    """The Appearance section states the currently active theme mode."""
    theme = ThemeManager()

    box = build_settings_view(theme)

    labels = [child.text for child in _all_labels(box)]
    assert "Theme: Light" in labels


def test_offers_a_button_to_switch_to_the_other_mode() -> None:
    """A button offers to switch to whichever mode isn't currently active."""
    theme = ThemeManager()

    box = build_settings_view(theme)

    button = _find_button(box, "Switch to Dark")
    assert button is not None


def test_pressing_the_toggle_button_switches_the_theme() -> None:
    """Pressing the switch button actually flips the theme manager's mode."""
    theme = ThemeManager()
    box = build_settings_view(theme)
    button = _find_button(box, "Switch to Dark")

    button._impl.simulate_press()

    assert theme.mode is ThemeMode.DARK


def _all_labels(box: toga.Box) -> list[toga.Label]:
    """Recursively collect every ``toga.Label`` under ``box``."""
    found: list[toga.Label] = []
    for child in box.children:
        if isinstance(child, toga.Label):
            found.append(child)
        if isinstance(child, toga.Box):
            found.extend(_all_labels(child))
    return found
