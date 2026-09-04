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
from pandaledger.views.transactions import build_transactions_view

#: Nav section labels in display order, paired with the factory that builds
#: that section's content box. A factory (rather than a pre-built widget) is
#: used because a Toga widget can only ever belong to one parent — each
#: section's box is built fresh the first time it's selected.
NAV_ITEMS: tuple[tuple[str, Callable[[], toga.Box]], ...] = (
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

    Args:
        app: The owning Toga application instance.
    """

    def __init__(self, app: toga.App) -> None:
        """Build the nav column and content pane, and select Dashboard.

        Args:
            app: The owning Toga application instance, used for its
                ``formal_name`` as the window title.
        """
        # toga.MainWindow.__init__ is declared as (*args, **kwargs) upstream
        # (toga 0.5.6), so mypy --strict can't verify this call.
        super().__init__(title=app.formal_name)  # type: ignore[no-untyped-call]
        self._content_pane = toga.Box(style=Pack(direction=COLUMN, flex=1))
        self._active_label: str | None = None

        nav_column = self._build_nav_column()
        self.content = toga.Box(
            children=[nav_column, self._content_pane],
            style=Pack(direction=ROW, flex=1),
        )
        self._select(NAV_ITEMS[0][0])

    def _build_nav_column(self) -> toga.Box:
        """Build the fixed-width left navigation column.

        Returns:
            A vertical ``toga.Box`` containing one button per top-level
            section, each wired to swap the content pane on press.
        """
        buttons = [
            toga.Button(
                label,
                on_press=self._make_nav_handler(label),
                style=Pack(margin=(4, 8)),
            )
            for label, _ in NAV_ITEMS
        ]
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
        """Swap the content pane to show the section for ``label``.

        Args:
            label: Section label to display; must match a key in
                ``NAV_ITEMS``.
        """
        if label == self._active_label:
            return
        build_view = dict(NAV_ITEMS)[label]
        self._content_pane.clear()
        self._content_pane.add(build_view())
        self._active_label = label
