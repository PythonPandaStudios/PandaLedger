"""Unit tests for :mod:`pandaledger.views.theme`."""

from __future__ import annotations

from pandaledger.views.theme import DARK_PALETTE, LIGHT_PALETTE, ThemeManager, ThemeMode


def test_defaults_to_light_mode() -> None:
    """A freshly constructed manager starts in light mode with the light palette."""
    theme = ThemeManager()

    assert theme.mode is ThemeMode.LIGHT
    assert theme.palette is LIGHT_PALETTE


def test_toggle_switches_mode_and_palette() -> None:
    """Toggling flips both the mode and the palette it reports."""
    theme = ThemeManager()

    theme.toggle()
    mode_after_first_toggle: ThemeMode = theme.mode

    assert mode_after_first_toggle is ThemeMode.DARK
    assert theme.palette is DARK_PALETTE

    theme.toggle()
    mode_after_second_toggle: ThemeMode = theme.mode

    assert mode_after_second_toggle is ThemeMode.LIGHT
    assert theme.palette is LIGHT_PALETTE


def test_set_mode_to_current_mode_does_not_notify_listeners() -> None:
    """Setting the mode that's already active is a no-op, including for listeners."""
    theme = ThemeManager()
    calls: list[object] = []
    theme.add_listener(calls.append)

    theme.set_mode(ThemeMode.LIGHT)

    assert calls == []


def test_toggle_notifies_every_registered_listener_with_new_palette() -> None:
    """All registered listeners fire, each receiving the newly active palette."""
    theme = ThemeManager()
    first_calls: list[object] = []
    second_calls: list[object] = []
    theme.add_listener(first_calls.append)
    theme.add_listener(second_calls.append)

    theme.toggle()

    assert first_calls == [DARK_PALETTE]
    assert second_calls == [DARK_PALETTE]


def test_starting_in_dark_mode_is_supported() -> None:
    """A manager can be constructed starting in dark mode."""
    theme = ThemeManager(initial_mode=ThemeMode.DARK)

    assert theme.mode is ThemeMode.DARK
    assert theme.palette is DARK_PALETTE
