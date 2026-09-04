"""Toga application entry point.

Wires the ``PandaLedgerApp`` instance to its main window. Kept intentionally
thin per the architecture in ``docs/PRD.md`` §5 — application wiring lives
here, screen layout lives in :mod:`pandaledger.views`, and business logic
lives in :mod:`pandaledger.controllers` / :mod:`pandaledger.models`.
"""

from __future__ import annotations

import toga
from sqlalchemy.orm import Session

from pandaledger.controllers.setup_controller import has_completed_first_run
from pandaledger.models.database import create_session_factory, create_sqlite_engine, init_db
from pandaledger.views.main_window import MainWindow
from pandaledger.views.theme import ThemeManager
from pandaledger.views.wizard.wizard_window import WizardWindow

#: Filename of the SQLite database within the platform's app-data directory.
DATABASE_FILENAME = "pandaledger.sqlite3"


class PandaLedgerApp(toga.App):
    """The PandaLedger desktop application."""

    def startup(self) -> None:
        """Set up the database, then show the wizard or the main window.

        Toga calls this once, after platform backend initialization, to
        let the app construct its first window(s). The theme manager and
        database are set up first, since both the wizard and the main
        window depend on them. A brand-new install (no Account exists
        yet) sees the first-run wizard (PRD §7.1) before the normal main
        window; a returning user goes straight to the main window.
        """
        self._theme = ThemeManager()
        engine = create_sqlite_engine(self.paths.data / DATABASE_FILENAME)
        init_db(engine)
        self._session = create_session_factory(engine)()

        if has_completed_first_run(self._session):
            self._show_main_window()
        else:
            wizard = WizardWindow(
                theme=self._theme,
                session=self._session,
                on_complete=self._show_main_window,
            )
            self.main_window = wizard
            wizard.show()

    def _show_main_window(self) -> None:
        """Build and show the persistent left-nav main window."""
        shell = MainWindow(formal_name=self.formal_name, theme=self._theme)
        self._shell = shell
        self.main_window = shell
        shell.show()

    @property
    def theme(self) -> ThemeManager:
        """The app's theme manager (PRD §7.1 light/dark theme)."""
        return self._theme

    @property
    def session(self) -> Session:
        """The app's long-lived database session."""
        return self._session

    @property
    def shell(self) -> MainWindow:
        """The app's persistent left-nav main window, typed as ``MainWindow``.

        ``toga.App.main_window`` is typed ``Window | str | None`` upstream to
        accommodate background-only apps, which loses the concrete type we
        know it always has here once the main window has been shown.

        Returns:
            The ``MainWindow`` instance created by :meth:`_show_main_window`.
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
