"""Application shell: persistent left-nav main window (PRD §7.1)."""

from __future__ import annotations

from collections.abc import Callable

import toga
from toga.style import Pack
from travertino.constants import COLUMN, ROW

from pandaledger.views.budget import build_budget_view
from pandaledger.views.dashboard import build_dashboard_view
from pandaledger.views.import_view import build_import_view
from pandaledger.views.paycheck import build_paycheck_view
from pandaledger.views.savings import build_savings_view
from pandaledger.views.settings import build_settings_view
from pandaledger.views.theme import Palette, ThemeManager
from pandaledger.views.transactions import build_transactions_view

#: Nav section labels in display order, paired with the factory that builds
#: that section's content box. A factory (rather than a pre-built widget) is
#: used because a Toga widget can only ever belong to one parent — each
#: section's box is built fresh every time it's selected, or when the theme
#: changes and the active section needs to be re-rendered in the new colors.
NAV_ITEMS: tuple[tuple[str, Callable[[ThemeManager], toga.Box]], ...] = (
    ("Dashboard", build_dashboard_view),
    ("Transactions", build_transactions_view),
    ("Budget", build_budget_view),
    ("Savings", build_savings_view),
    ("Paycheck", build_paycheck_view),
    ("Import", build_import_view),
    ("Settings", build_settings_view),
)

#: Fixed width, in CSS pixels, of the left navigation column.
NAV_COLUMN_WIDTH = 180


class MainWindow(toga.MainWindow):
    """Persistent left-nav application shell.

    Builds a two-pane layout: a fixed-width left navigation column listing
    the app's top-level sections (Dashboard / Transactions / Budget /
    Savings / Paycheck / Import / Settings), and a right content pane that
    swaps between per-section view boxes as the user clicks a nav entry.
    Registers itself as a theme listener so a light/dark switch (from the
    Settings screen) re-colors the nav chrome and re-renders whichever
    section is currently showing.

    Args:
        formal_name: The app's display name, used as the window title.
        theme: The app's theme manager, shared with every screen this
            window renders.
    """

    def __init__(self, formal_name: str, theme: ThemeManager) -> None:
        """Build the nav column and content pane, and select Dashboard.

        Args:
            formal_name: The app's display name, used as the window title.
            theme: The app's theme manager.
        """
        # toga.MainWindow.__init__ is declared as (*args, **kwargs) upstream
        # (toga 0.5.6), so mypy --strict can't verify this call.
        super().__init__(title=formal_name)  # type: ignore[no-untyped-call]
        self._theme = theme
        self._nav_buttons: dict[str, toga.Button] = {}
        self._content_pane = toga.Box(style=Pack(direction=COLUMN, flex=1))
        self._active_label: str | None = None

        self._nav_column = self._build_nav_column()
        self._root = toga.Box(
            children=[self._nav_column, self._content_pane],
            style=Pack(direction=ROW, flex=1),
        )
        self.content = self._root
        self._active_label = NAV_ITEMS[0][0]
        self._render_content()
        self._style_chrome(theme.palette)
        theme.add_listener(self._on_theme_changed)

    def _build_nav_column(self) -> toga.Box:
        """Build the fixed-width left navigation column.

        Returns:
            A vertical ``toga.Box`` containing one button per top-level
            section, each wired to swap the content pane on press.
        """
        buttons = []
        for label, _ in NAV_ITEMS:
            button = toga.Button(
                label,
                on_press=self._make_nav_handler(label),
                style=Pack(margin=(4, 8)),
            )
            self._nav_buttons[label] = button
            buttons.append(button)
        return toga.Box(
            children=buttons,
            style=Pack(direction=COLUMN, width=NAV_COLUMN_WIDTH, margin=8),
        )

    def _make_nav_handler(self, label: str) -> Callable[[toga.Widget], None]:
        """Build an ``on_press`` handler bound to a specific nav label.

        A closure factory is needed here rather than one shared handler
        because Toga's ``on_press`` callback only receives the pressed
        widget, not which nav item it represents.

        Args:
            label: The section label the returned handler should select.

        Returns:
            A callback suitable for a Toga ``Button``'s ``on_press``.
        """

        def handler(widget: toga.Widget) -> None:
            self._select(label)

        return handler

    def _select(self, label: str) -> None:
        """Switch the content pane to show the section for ``label``.

        Args:
            label: Section label to display; must match a key in
                ``NAV_ITEMS``.
        """
        if label == self._active_label:
            return
        self._active_label = label
        self._render_content()

    def _render_content(self) -> None:
        """Rebuild the content pane from the currently active nav label.

        Called both when the user picks a different section and when the
        theme changes and the *same* section needs to be redrawn in the new
        palette — a Toga widget can only belong to one parent, so "redraw"
        means discarding the old box and building a fresh one.
        """
        label = self._active_label
        assert label is not None, "_render_content called before a section was selected"
        build_view = dict(NAV_ITEMS)[label]
        self._content_pane.clear()
        self._content_pane.add(build_view(self._theme))

    def _style_chrome(self, palette: Palette) -> None:
        """Apply ``palette`` to the window chrome.

        Args:
            palette: The palette to apply (PRD §7.1 light/dark theme).

        Note:
            The nav column is styled with its *own* ``background_color``,
            but that box only ever sizes itself to its buttons' natural
            height — in Toga's Pack layout, only the sibling with the
            largest ``flex`` value stretches to fill the row's full height,
            and a sibling with an explicit ``width`` never does regardless
            of its own ``flex``. So the nav column's surface color would
            leave an unstyled gap below the last button. The fix is to
            color the root row instead: a window's top-level content box
            always fills the window, so the root's color shows through
            everywhere the (fully-stretched) content pane doesn't opaquely
            cover it — including that gap.
        """
        self._root.style.background_color = palette.surface
        self._nav_column.style.background_color = palette.surface
        self._content_pane.style.background_color = palette.background
        for button in self._nav_buttons.values():
            button.style.background_color = palette.surface
            button.style.color = palette.text

    def _on_theme_changed(self, palette: Palette) -> None:
        """React to a theme switch: re-style the chrome and current section.

        Args:
            palette: The newly active palette.
        """
        self._style_chrome(palette)
        self._render_content()
