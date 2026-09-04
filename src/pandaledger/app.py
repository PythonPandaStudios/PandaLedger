"""Toga application entry point.

Wires the ``PandaLedgerApp`` instance to its main window. Kept intentionally
thin per the architecture in ``docs/PRD.md`` §5 — application wiring lives
here, screen layout lives in :mod:`pandaledger.views`, and business logic
lives in :mod:`pandaledger.controllers` / :mod:`pandaledger.models`.
"""

from __future__ import annotations

import toga

from pandaledger.views.main_window import MainWindow


class PandaLedgerApp(toga.App):
    """The PandaLedger desktop application."""

    def startup(self) -> None:
        """Build and show the main window.

        Toga calls this once, after platform backend initialization, to let
        the app construct its first window(s).
        """
        shell = MainWindow(app=self)
        self._shell = shell
        self.main_window = shell
        shell.show()

    @property
    def shell(self) -> MainWindow:
        """The app's persistent left-nav main window, typed as ``MainWindow``.

        ``toga.App.main_window`` is typed ``Window | str | None`` upstream to
        accommodate background-only apps, which loses the concrete type we
        know it always has here once :meth:`startup` has run.

        Returns:
            The ``MainWindow`` instance created during :meth:`startup`.
        """
        return self._shell


def main() -> PandaLedgerApp:
    """Construct the application instance.

    This is the callable Briefcase/``__main__`` invoke to obtain the app;
    Toga itself calls :meth:`PandaLedgerApp.startup` once the event loop
    starts running it.

    Returns:
        A configured, not-yet-started ``PandaLedgerApp`` instance.
    """
    return PandaLedgerApp(
        formal_name="PandaLedger",
        app_id="studios.pythonpanda.pandaledger",
    )
