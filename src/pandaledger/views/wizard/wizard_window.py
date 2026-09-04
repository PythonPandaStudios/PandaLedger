"""First-run setup wizard orchestration (PRD §7.1).

Walks a brand-new user through: create an Account → pick a Budget
strategy → pick a Savings strategy → optionally set up an IncomeSource.
Shown once, before the main window, on any launch where
:func:`pandaledger.controllers.setup_controller.has_completed_first_run`
is ``False``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

import toga
from sqlalchemy.orm import Session
from toga.style import Pack
from travertino.constants import COLUMN, ROW

from pandaledger.controllers.setup_controller import (
    create_first_account,
    create_income_source,
    set_budget_strategy,
    set_savings_strategy,
)
from pandaledger.views.theme import Palette, ThemeManager
from pandaledger.views.wizard.account_step import AccountStep
from pandaledger.views.wizard.budget_strategy_step import BudgetStrategyStep
from pandaledger.views.wizard.income_source_step import IncomeSourceStep
from pandaledger.views.wizard.savings_strategy_step import SavingsStrategyStep


class WizardStep(Protocol):
    """What every wizard step must provide, for navigation purposes."""

    title: str

    def build(self, palette: Palette) -> toga.Box:
        """Build this step's form content."""
        ...

    def validate(self) -> str | None:
        """Return a user-facing error message, or ``None`` if valid."""
        ...


class WizardWindow(toga.MainWindow):
    """A standalone first-run window that walks through setup, one step at a time.

    Subclasses ``MainWindow`` rather than the plain ``Window`` base: Toga's
    own ``App._startup()`` unconditionally requires ``app.main_window`` to
    be assigned to something before it returns (raising ``ValueError`` if
    it's never set at all — a stricter check than "no windows open"), and
    ``App.main_window``'s setter only accepts a ``MainWindow``. Being shown
    as the temporary main window is otherwise no different from any other
    window; it hands off to the real ``MainWindow`` on completion.

    Args:
        theme: The app's theme manager, for styling each step.
        session: Database session everything gets persisted through on
            the final "Finish" press.
        on_complete: Called once the wizard has persisted everything and
            closed itself, so the caller can show the normal main window.
    """

    def __init__(
        self,
        theme: ThemeManager,
        session: Session,
        on_complete: Callable[[], None],
    ) -> None:
        """Build the wizard's chrome and render its first step.

        Args:
            theme: The app's theme manager.
            session: Database session to persist through on completion.
            on_complete: Called after a successful finish.
        """
        # toga.MainWindow.__init__ is declared as (*args, **kwargs) upstream
        # (toga 0.5.6), so mypy --strict can't verify this call.
        super().__init__(  # type: ignore[no-untyped-call]
            title="Welcome to PandaLedger", size=(640, 520)
        )
        self._theme = theme
        self._session = session
        self._on_complete = on_complete

        self._account_step = AccountStep()
        self._budget_step = BudgetStrategyStep()
        self._savings_step = SavingsStrategyStep()
        self._income_step = IncomeSourceStep()
        self._steps: list[WizardStep] = [
            self._account_step,
            self._budget_step,
            self._savings_step,
            self._income_step,
        ]
        self._step_index = 0

        self._step_pane = toga.Box(style=Pack(direction=COLUMN, flex=1))
        self._error_label = toga.Label("", style=Pack(color="#b00020", margin_bottom=8))
        self._back_button = toga.Button("Back", on_press=self._on_back)
        self._next_button = toga.Button("Next", on_press=self._on_next)
        button_row = toga.Box(
            children=[self._back_button, self._next_button],
            style=Pack(direction=ROW),
        )
        self.content = toga.Box(
            children=[self._step_pane, self._error_label, button_row],
            # Every child box below is transparent by default, so this is
            # what actually paints the window — without it, GTK's own
            # (dark, on this theme) native background shows through behind
            # text colored for the light palette, same underlying issue as
            # the main window's nav column (see main_window.py's
            # _style_chrome docstring).
            style=Pack(
                direction=COLUMN,
                background_color=theme.palette.background,
                margin=16,
                flex=1,
            ),
        )
        self._render_step()

    def _render_step(self) -> None:
        """Rebuild the step pane for the currently active step and update chrome."""
        step = self._steps[self._step_index]
        self._step_pane.clear()
        self._step_pane.add(step.build(self._theme.palette))
        self._error_label.text = ""
        self._back_button.enabled = self._step_index > 0
        self._next_button.text = "Finish" if self._is_last_step() else "Next"

    def _is_last_step(self) -> bool:
        """Whether the currently active step is the last one."""
        return self._step_index == len(self._steps) - 1

    def _on_back(self, widget: toga.Widget) -> None:
        """Go back one step, if not already on the first one.

        Args:
            widget: The pressed button (unused).
        """
        if self._step_index > 0:
            self._step_index -= 1
            self._render_step()

    def _on_next(self, widget: toga.Widget) -> None:
        """Validate the current step, then advance or finish.

        Args:
            widget: The pressed button (unused).
        """
        step = self._steps[self._step_index]
        error = step.validate()
        if error is not None:
            self._error_label.text = error
            return
        if self._is_last_step():
            self._finish()
        else:
            self._step_index += 1
            self._render_step()

    def _finish(self) -> None:
        """Persist everything collected, close the wizard, and hand off to the caller."""
        account_result = self._account_step.result
        create_first_account(
            self._session,
            institution_name=account_result.institution_name,
            institution_kind=account_result.institution_kind,
            account_name=account_result.account_name,
            account_type=account_result.account_type,
            current_balance_cents=account_result.current_balance_cents,
        )
        set_budget_strategy(self._session, self._budget_step.result)
        set_savings_strategy(self._session, self._savings_step.result)

        income_result = self._income_step.result
        if income_result is not None:
            create_income_source(
                self._session,
                name=income_result.name,
                income_type=income_result.income_type,
                rate_cents=income_result.rate_cents,
                schedule=income_result.schedule,
                filing_status=income_result.filing_status,
                state_code=income_result.state_code,
            )

        self._session.commit()
        # on_complete (PandaLedgerApp._show_main_window) must run BEFORE
        # close(): Window.close() on whichever window is currently
        # app.main_window doesn't just close it — it calls
        # app.request_exit(), quitting the whole app, since Toga treats
        # closing "the" main window as a request to exit. on_complete
        # reassigns app.main_window to the real shell first, so closing
        # the wizard afterward is just closing an ordinary window.
        self._on_complete()
        self.close()
