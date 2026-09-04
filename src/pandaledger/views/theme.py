"""Light/dark theme support for the Toga UI (PRD §7.1).

Toga has no stylesheet mechanism like Qt did in the previous prototype, so
"theme" here means a small palette of hex color tokens that view code reads
when building its ``Pack`` styles, plus a manager that lets any screen
switch the active palette at runtime and have already-built screens
re-render with it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class ThemeMode(Enum):
    """The two supported theme modes."""

    LIGHT = "light"
    DARK = "dark"


@dataclass(frozen=True)
class Palette:
    """A set of hex color tokens views use for backgrounds, text, etc.

    Attributes:
        background: Main content-area background.
        surface: Background for a visually distinct panel, e.g. the nav
            column, set apart from the main content background.
        text: Primary text color.
        text_muted: Secondary/supporting text color (empty-state copy,
            captions).
        accent: Interactive/highlight color (buttons, selected state).
        border: Hairline border/divider color.
    """

    background: str
    surface: str
    text: str
    text_muted: str
    accent: str
    border: str


#: Default palette — used in normal daylight/light-desktop-theme conditions.
LIGHT_PALETTE = Palette(
    background="#ffffff",
    surface="#eeeeee",
    text="#1b1b1b",
    text_muted="#5a5a5a",
    accent="#2f6f4f",
    border="#d9d9d9",
)

#: Palette used when the user switches to dark mode.
DARK_PALETTE = Palette(
    background="#1e1e1e",
    surface="#262626",
    text="#ececec",
    text_muted="#a8a8a8",
    accent="#6fbf8b",
    border="#3a3a3a",
)

_PALETTES: dict[ThemeMode, Palette] = {
    ThemeMode.LIGHT: LIGHT_PALETTE,
    ThemeMode.DARK: DARK_PALETTE,
}


class ThemeManager:
    """Tracks the active theme mode and notifies listeners when it changes.

    Any view that wants to react live to a theme switch (rather than just
    reading the palette once at build time) registers a listener via
    :meth:`add_listener`; :meth:`toggle` and :meth:`set_mode` call every
    registered listener with the new palette.
    """

    def __init__(self, initial_mode: ThemeMode = ThemeMode.LIGHT) -> None:
        """Initialize the manager with a starting mode.

        Args:
            initial_mode: The mode to start in. Defaults to light; PandaLedger
                v1 does not attempt to auto-detect the OS/desktop theme (no
                portable Toga API for that as of 0.5.6), so the user picks
                explicitly from Settings.
        """
        self._mode = initial_mode
        self._listeners: list[Callable[[Palette], None]] = []

    @property
    def mode(self) -> ThemeMode:
        """The currently active theme mode."""
        return self._mode

    @property
    def palette(self) -> Palette:
        """The color palette for the currently active mode."""
        return _PALETTES[self._mode]

    def add_listener(self, callback: Callable[[Palette], None]) -> None:
        """Register a callback to run whenever the active palette changes.

        Args:
            callback: Called with the new ``Palette`` immediately after a
                mode change. Not called immediately upon registration —
                callers should read :attr:`palette` directly for the
                initial render.
        """
        self._listeners.append(callback)

    def set_mode(self, mode: ThemeMode) -> None:
        """Switch to ``mode`` and notify listeners, if it's actually a change.

        Args:
            mode: The mode to switch to.
        """
        if mode == self._mode:
            return
        self._mode = mode
        for listener in self._listeners:
            listener(self.palette)

    def toggle(self) -> None:
        """Switch from light to dark or vice versa."""
        next_mode = ThemeMode.DARK if self._mode is ThemeMode.LIGHT else ThemeMode.LIGHT
        self.set_mode(next_mode)
