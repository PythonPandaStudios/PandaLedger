"""Unit tests for :mod:`pandaledger.views.wizard.wizard_window`."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
import toga
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from pandaledger.models.database import create_session_factory, create_sqlite_engine, init_db
from pandaledger.models.schema import Account, Config, IncomeSource
from pandaledger.views.theme import ThemeManager
from pandaledger.views.wizard.wizard_window import WizardWindow


@pytest.fixture
def engine(tmp_path) -> Iterator[Engine]:  # type: ignore[no-untyped-def]
    engine = create_sqlite_engine(tmp_path / "pandaledger.sqlite3")
    init_db(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        yield session


@pytest.fixture
def completions() -> list[bool]:
    """Records each ``on_complete`` call a test's wizard makes."""
    return []


@pytest.fixture
def _hosting_app() -> toga.App:
    """A minimal running App — a Window can't be created without one.

    Its own default ``startup()`` creates and shows a throwaway
    ``MainWindow``, which these tests otherwise ignore; the ``WizardWindow``
    under test is a separate window shown on top of it.
    """
    return toga.App(formal_name="WizardWindow Test Host", app_id="test.wizard_window")


@pytest.fixture
def wizard(session: Session, completions: list[bool], _hosting_app: toga.App) -> WizardWindow:
    return WizardWindow(
        theme=ThemeManager(), session=session, on_complete=lambda: completions.append(True)
    )


def _fill_account_step(wizard: WizardWindow) -> None:
    wizard._account_step._institution_name_input.value = "Capital One"
    wizard._account_step._account_name_input.value = "Checking"
    wizard._account_step._balance_input.value = "500.00"


class TestNavigation:
    def test_starts_on_the_account_step(self, wizard: WizardWindow) -> None:
        assert wizard._step_index == 0
        assert wizard._back_button.enabled is False
        assert wizard._next_button.text == "Next"

    def test_next_is_blocked_when_the_current_step_is_invalid(self, wizard: WizardWindow) -> None:
        wizard._on_next(wizard._next_button)

        assert wizard._step_index == 0
        assert wizard._error_label.text != ""

    def test_next_advances_once_the_step_is_valid(self, wizard: WizardWindow) -> None:
        _fill_account_step(wizard)

        wizard._on_next(wizard._next_button)

        assert wizard._step_index == 1
        assert wizard._error_label.text == ""

    def test_back_returns_to_the_previous_step(self, wizard: WizardWindow) -> None:
        _fill_account_step(wizard)
        wizard._on_next(wizard._next_button)

        wizard._on_back(wizard._back_button)

        assert wizard._step_index == 0
        assert wizard._back_button.enabled is False

    def test_back_is_a_no_op_on_the_first_step(self, wizard: WizardWindow) -> None:
        wizard._on_back(wizard._back_button)

        assert wizard._step_index == 0

    def test_last_step_shows_finish_instead_of_next(self, wizard: WizardWindow) -> None:
        _fill_account_step(wizard)
        wizard._on_next(wizard._next_button)  # -> budget strategy
        wizard._on_next(wizard._next_button)  # -> savings strategy
        wizard._on_next(wizard._next_button)  # -> income source (last)

        assert wizard._next_button.text == "Finish"


class TestFinish:
    def test_finishing_persists_account_and_strategies(
        self, wizard: WizardWindow, session: Session
    ) -> None:
        _fill_account_step(wizard)
        wizard._on_next(wizard._next_button)  # -> budget strategy
        wizard._on_next(wizard._next_button)  # -> savings strategy
        wizard._on_next(wizard._next_button)  # -> income source (last), income left off

        wizard._on_next(wizard._next_button)  # Finish

        account = session.execute(select(Account)).scalar_one()
        assert account.name == "Checking"
        assert account.institution.name == "Capital One"
        budget_config = session.get(Config, "budget_strategy")
        assert budget_config is not None
        assert budget_config.value == "rolling_average"
        savings_config = session.get(Config, "savings_strategy")
        assert savings_config is not None
        assert savings_config.value == "pay_yourself_first"

    def test_finish_calls_on_complete(self, wizard: WizardWindow, completions: list[bool]) -> None:
        _fill_account_step(wizard)
        wizard._on_next(wizard._next_button)
        wizard._on_next(wizard._next_button)
        wizard._on_next(wizard._next_button)

        wizard._on_next(wizard._next_button)  # Finish

        assert completions == [True]

    def test_finish_without_an_income_source_creates_none(
        self, wizard: WizardWindow, session: Session
    ) -> None:
        _fill_account_step(wizard)
        wizard._on_next(wizard._next_button)
        wizard._on_next(wizard._next_button)
        wizard._on_next(wizard._next_button)

        wizard._on_next(wizard._next_button)  # Finish, income source switch left off

        assert session.execute(select(IncomeSource)).first() is None

    def test_finish_with_an_income_source_persists_it(
        self, wizard: WizardWindow, session: Session
    ) -> None:
        _fill_account_step(wizard)
        wizard._on_next(wizard._next_button)
        wizard._on_next(wizard._next_button)
        wizard._on_next(wizard._next_button)
        wizard._income_step._enabled_switch.value = True
        wizard._income_step._name_input.value = "Commdex"
        wizard._income_step._rate_input.value = "80000"
        wizard._income_step._state_code_input.value = "CO"

        wizard._on_next(wizard._next_button)  # Finish

        income_source = session.execute(select(IncomeSource)).scalar_one()
        assert income_source.name == "Commdex"

    def test_finish_is_blocked_if_the_income_source_step_is_invalid(
        self, wizard: WizardWindow, session: Session
    ) -> None:
        _fill_account_step(wizard)
        wizard._on_next(wizard._next_button)
        wizard._on_next(wizard._next_button)
        wizard._on_next(wizard._next_button)
        wizard._income_step._enabled_switch.value = True
        # Name left blank -> invalid.

        wizard._on_next(wizard._next_button)

        assert wizard._step_index == 3
        assert wizard._error_label.text != ""
        assert session.execute(select(Account)).first() is None
