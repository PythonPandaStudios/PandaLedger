"""Unit tests for :mod:`pandaledger.controllers.setup_controller`."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from pandaledger.controllers.setup_controller import (
    BUDGET_STRATEGY_CONFIG_KEY,
    SAVINGS_STRATEGY_CONFIG_KEY,
    create_first_account,
    create_income_source,
    has_completed_first_run,
    set_budget_strategy,
    set_savings_strategy,
)
from pandaledger.models.database import create_session_factory, create_sqlite_engine, init_db
from pandaledger.models.schema import (
    AccountType,
    BudgetStrategy,
    Config,
    FilingStatus,
    IncomeType,
    InstitutionKind,
    PayScheduleType,
    SavingsStrategy,
)


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


class TestHasCompletedFirstRun:
    def test_false_on_a_fresh_database(self, session: Session) -> None:
        assert has_completed_first_run(session) is False

    def test_true_once_an_account_exists(self, session: Session) -> None:
        create_first_account(
            session,
            institution_name="Capital One",
            institution_kind=InstitutionKind.BANK,
            account_name="Checking",
            account_type=AccountType.CHECKING,
            current_balance_cents=10_000,
        )

        assert has_completed_first_run(session) is True


class TestCreateFirstAccount:
    def test_creates_institution_and_account_together(self, session: Session) -> None:
        account = create_first_account(
            session,
            institution_name="Capital One",
            institution_kind=InstitutionKind.BANK,
            account_name="Checking",
            account_type=AccountType.CHECKING,
            current_balance_cents=10_000,
        )

        assert account.id is not None
        assert account.institution.name == "Capital One"
        assert account.institution.kind is InstitutionKind.BANK
        assert account.current_balance_cents == 10_000

    def test_negative_starting_balance_is_allowed(self, session: Session) -> None:
        """An overdrawn checking account is a real starting state, not an error."""
        account = create_first_account(
            session,
            institution_name="Capital One",
            institution_kind=InstitutionKind.BANK,
            account_name="Checking",
            account_type=AccountType.CHECKING,
            current_balance_cents=-500,
        )

        assert account.current_balance_cents == -500

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_blank_institution_name_is_rejected(self, session: Session, blank: str) -> None:
        with pytest.raises(ValueError, match="institution_name"):
            create_first_account(
                session,
                institution_name=blank,
                institution_kind=InstitutionKind.BANK,
                account_name="Checking",
                account_type=AccountType.CHECKING,
                current_balance_cents=0,
            )

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_blank_account_name_is_rejected(self, session: Session, blank: str) -> None:
        with pytest.raises(ValueError, match="account_name"):
            create_first_account(
                session,
                institution_name="Capital One",
                institution_kind=InstitutionKind.BANK,
                account_name=blank,
                account_type=AccountType.CHECKING,
                current_balance_cents=0,
            )


class TestStrategyConfig:
    def test_set_budget_strategy_creates_the_config_row(self, session: Session) -> None:
        set_budget_strategy(session, BudgetStrategy.ROLLING_AVERAGE)

        stored = session.get(Config, BUDGET_STRATEGY_CONFIG_KEY)
        assert stored is not None
        assert stored.value == "rolling_average"

    def test_set_budget_strategy_overwrites_a_prior_choice(self, session: Session) -> None:
        set_budget_strategy(session, BudgetStrategy.ROLLING_AVERAGE)

        set_budget_strategy(session, BudgetStrategy.ZERO_BASED)

        stored = session.get(Config, BUDGET_STRATEGY_CONFIG_KEY)
        assert stored is not None
        assert stored.value == "zero_based"

    def test_set_savings_strategy_creates_the_config_row(self, session: Session) -> None:
        set_savings_strategy(session, SavingsStrategy.EMERGENCY_FUND)

        stored = session.get(Config, SAVINGS_STRATEGY_CONFIG_KEY)
        assert stored is not None
        assert stored.value == "emergency_fund"


class TestCreateIncomeSource:
    def test_creates_an_income_source(self, session: Session) -> None:
        income_source = create_income_source(
            session,
            name="Commdex",
            income_type=IncomeType.SALARY,
            rate_cents=8_000_000,
            schedule=PayScheduleType.BIWEEKLY,
            filing_status=FilingStatus.SINGLE,
            state_code="co",
        )

        assert income_source.name == "Commdex"
        assert income_source.state_code == "CO"  # normalized to uppercase

    def test_blank_name_is_rejected(self, session: Session) -> None:
        with pytest.raises(ValueError, match="name"):
            create_income_source(
                session,
                name="  ",
                income_type=IncomeType.SALARY,
                rate_cents=8_000_000,
                schedule=PayScheduleType.BIWEEKLY,
                filing_status=FilingStatus.SINGLE,
                state_code="CO",
            )

    @pytest.mark.parametrize("rate_cents", [0, -100])
    def test_non_positive_rate_is_rejected(self, session: Session, rate_cents: int) -> None:
        with pytest.raises(ValueError, match="rate_cents"):
            create_income_source(
                session,
                name="Commdex",
                income_type=IncomeType.SALARY,
                rate_cents=rate_cents,
                schedule=PayScheduleType.BIWEEKLY,
                filing_status=FilingStatus.SINGLE,
                state_code="CO",
            )

    @pytest.mark.parametrize("state_code", ["C", "COL", ""])
    def test_invalid_state_code_is_rejected(self, session: Session, state_code: str) -> None:
        with pytest.raises(ValueError, match="state_code"):
            create_income_source(
                session,
                name="Commdex",
                income_type=IncomeType.SALARY,
                rate_cents=8_000_000,
                schedule=PayScheduleType.BIWEEKLY,
                filing_status=FilingStatus.SINGLE,
                state_code=state_code,
            )
