"""Unit tests for :mod:`pandaledger.models.schema`."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pandaledger.models.database import create_session_factory, create_sqlite_engine, init_db
from pandaledger.models.schema import (
    Account,
    AccountType,
    BudgetLine,
    BudgetPlan,
    BudgetStrategy,
    CategorizationRule,
    Category,
    CategoryType,
    Config,
    Deduction,
    DeductionCategory,
    FilingStatus,
    ImportBatch,
    IncomeSource,
    IncomeType,
    Institution,
    InstitutionKind,
    MatchType,
    PayScheduleType,
    RecurrenceFrequency,
    RecurringTransaction,
    SavingsGoal,
    SavingsStrategy,
    Transaction,
)


@pytest.fixture
def engine(tmp_path) -> Iterator[Engine]:  # type: ignore[no-untyped-def]
    """An initialized, on-disk SQLite engine with foreign keys enforced."""
    engine = create_sqlite_engine(tmp_path / "pandaledger.sqlite3")
    init_db(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    """A session bound to the test engine, closed after each test."""
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        yield session


def _make_institution(session: Session, name: str = "Capital One") -> Institution:
    institution = Institution(name=name, kind=InstitutionKind.BANK)
    session.add(institution)
    session.flush()
    return institution


def _make_account(session: Session, institution: Institution | None = None) -> Account:
    account = Account(
        institution=institution or _make_institution(session),
        name="Checking",
        type=AccountType.CHECKING,
        current_balance_cents=10_000,
    )
    session.add(account)
    session.flush()
    return account


class TestSyncedMixinBehavior:
    def test_id_is_auto_generated_and_unique(self, session: Session) -> None:
        """Every row gets a distinct UUID primary key without being told to."""
        first = _make_institution(session, "Bank A")
        second = _make_institution(session, "Bank B")

        assert first.id != second.id
        assert len(first.id) == 36  # standard hyphenated UUID string length

    def test_updated_at_is_set_on_insert(self, session: Session) -> None:
        # updated_at is naive-but-UTC by convention (see schema._utcnow), so
        # the comparison value must be naive too.
        before = dt.datetime.now(dt.UTC).replace(tzinfo=None)

        institution = _make_institution(session)

        assert institution.updated_at >= before

    def test_updated_at_changes_on_update(self, session: Session) -> None:
        institution = _make_institution(session)
        original_updated_at = institution.updated_at
        session.commit()

        institution.name = "Renamed Bank"
        session.commit()

        assert institution.updated_at > original_updated_at

    def test_deleted_at_defaults_to_none(self, session: Session) -> None:
        institution = _make_institution(session)

        assert institution.deleted_at is None


class TestRelationshipsAndForeignKeys:
    def test_account_requires_a_real_institution(self, session: Session) -> None:
        """A bogus institution_id is rejected by SQLite's FK enforcement."""
        account = Account(
            institution_id="not-a-real-institution-id",
            name="Checking",
            type=AccountType.CHECKING,
            current_balance_cents=0,
        )
        session.add(account)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_account_institution_relationship_round_trips(self, session: Session) -> None:
        institution = _make_institution(session)
        account = _make_account(session, institution)
        session.commit()
        session.expire_all()

        reloaded = session.get(Account, account.id)
        assert reloaded is not None
        assert reloaded.institution.name == "Capital One"
        assert reloaded in institution.accounts

    def test_category_self_referential_parent_and_children(self, session: Session) -> None:
        parent = Category(name="Food", type=CategoryType.VARIABLE, user_created=False)
        child = Category(
            name="Groceries", type=CategoryType.VARIABLE, user_created=False, parent=parent
        )
        session.add_all([parent, child])
        session.commit()
        session.expire_all()

        reloaded_parent = session.get(Category, parent.id)
        assert reloaded_parent is not None
        assert [c.name for c in reloaded_parent.children] == ["Groceries"]
        reloaded_child = session.get(Category, child.id)
        assert reloaded_child is not None
        assert reloaded_child.parent is not None
        assert reloaded_child.parent.name == "Food"

    def test_transaction_split_via_parent_transaction_id(self, session: Session) -> None:
        account = _make_account(session)
        parent_txn = Transaction(
            account=account,
            date=dt.date(2026, 1, 15),
            payee="Costco",
            amount_cents=-15_000,
            dedupe_hash="hash-parent",
        )
        session.add(parent_txn)
        session.flush()
        child_txn = Transaction(
            account=account,
            date=parent_txn.date,
            payee="Costco (Groceries split)",
            amount_cents=-10_000,
            dedupe_hash="hash-child-1",
            parent_transaction_id=parent_txn.id,
        )
        session.add(child_txn)
        session.commit()
        session.expire_all()

        reloaded_parent = session.get(Transaction, parent_txn.id)
        assert reloaded_parent is not None
        assert [c.payee for c in reloaded_parent.children] == ["Costco (Groceries split)"]

    def test_dedupe_hash_is_unique_per_account(self, session: Session) -> None:
        """Re-importing the same statement line must not create a duplicate row."""
        account = _make_account(session)
        session.add(
            Transaction(
                account=account,
                date=dt.date(2026, 1, 1),
                payee="Costco",
                amount_cents=-5_000,
                dedupe_hash="same-hash",
            )
        )
        session.commit()

        session.add(
            Transaction(
                account=account,
                date=dt.date(2026, 1, 1),
                payee="Costco",
                amount_cents=-5_000,
                dedupe_hash="same-hash",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()

    def test_dedupe_hash_can_repeat_across_different_accounts(self, session: Session) -> None:
        """The uniqueness constraint is scoped per-account, not global."""
        institution = _make_institution(session)
        account_a = _make_account(session, institution)
        account_b = Account(
            institution=institution,
            name="Savings",
            type=AccountType.SAVINGS,
            current_balance_cents=0,
        )
        session.add(account_b)
        session.flush()

        session.add(
            Transaction(
                account=account_a,
                date=dt.date(2026, 1, 1),
                payee="Costco",
                amount_cents=-5_000,
                dedupe_hash="shared-hash",
            )
        )
        session.add(
            Transaction(
                account=account_b,
                date=dt.date(2026, 1, 1),
                payee="Costco",
                amount_cents=-5_000,
                dedupe_hash="shared-hash",
            )
        )

        session.commit()  # should not raise

    def test_recurring_transaction_round_trips(self, session: Session) -> None:
        account = _make_account(session)
        recurring = RecurringTransaction(
            account=account,
            payee="Rent",
            amount_cents=-150_000,
            frequency=RecurrenceFrequency.MONTHLY,
            next_due_date=dt.date(2026, 10, 1),
        )
        session.add(recurring)
        session.commit()
        session.expire_all()

        reloaded = session.get(RecurringTransaction, recurring.id)
        assert reloaded is not None
        assert reloaded.frequency is RecurrenceFrequency.MONTHLY
        assert reloaded.account.name == "Checking"

    def test_categorization_rule_can_reference_its_originating_transaction(
        self, session: Session
    ) -> None:
        account = _make_account(session)
        category = Category(name="Groceries", type=CategoryType.VARIABLE, user_created=True)
        session.add(category)
        txn = Transaction(
            account=account,
            date=dt.date(2026, 1, 1),
            payee="Costco",
            amount_cents=-5_000,
            dedupe_hash="hash-1",
            category=category,
        )
        session.add(txn)
        session.flush()

        rule = CategorizationRule(
            pattern="Costco",
            match_type=MatchType.SUBSTRING,
            category=category,
            created_from_transaction=txn,
        )
        session.add(rule)
        session.commit()
        session.expire_all()

        reloaded = session.get(CategorizationRule, rule.id)
        assert reloaded is not None
        assert reloaded.created_from_transaction is not None
        assert reloaded.created_from_transaction.payee == "Costco"


class TestIncomeAndDeductions:
    def test_income_source_with_pre_tax_percent_deduction(self, session: Session) -> None:
        income_source = IncomeSource(
            name="Commdex",
            income_type=IncomeType.SALARY,
            rate_cents=8_000_000,
            schedule=PayScheduleType.BIWEEKLY,
            filing_status=FilingStatus.SINGLE,
            state_code="CO",
        )
        deduction = Deduction(
            income_source=income_source,
            name="401k",
            amount_cents_or_percent=525,  # 5.25%, in basis points
            is_percent=True,
            is_pre_tax=True,
            category=DeductionCategory.RETIREMENT_401K,
        )
        session.add_all([income_source, deduction])
        session.commit()
        session.expire_all()

        reloaded = session.get(IncomeSource, income_source.id)
        assert reloaded is not None
        assert len(reloaded.deductions) == 1
        assert reloaded.deductions[0].amount_cents_or_percent == 525


class TestBudgetAndSavings:
    def test_budget_plan_with_lines(self, session: Session) -> None:
        category = Category(name="Groceries", type=CategoryType.VARIABLE, user_created=True)
        plan = BudgetPlan(month=10, year=2026, strategy=BudgetStrategy.ROLLING_AVERAGE)
        line = BudgetLine(
            budget_plan=plan, category=category, suggested_cents=40_000, approved_cents=40_000
        )
        session.add_all([category, plan, line])
        session.commit()
        session.expire_all()

        reloaded = session.get(BudgetPlan, plan.id)
        assert reloaded is not None
        assert len(reloaded.lines) == 1
        assert reloaded.lines[0].category.name == "Groceries"

    def test_savings_goal_round_trips(self, session: Session) -> None:
        goal = SavingsGoal(
            strategy=SavingsStrategy.EMERGENCY_FUND,
            strategy_config={"target_months": 3},
            target_cents=1_500_000,
            current_cents=250_000,
        )
        session.add(goal)
        session.commit()
        session.expire_all()

        reloaded = session.get(SavingsGoal, goal.id)
        assert reloaded is not None
        assert reloaded.strategy_config == {"target_months": 3}


class TestConfig:
    def test_config_is_a_plain_key_value_row_without_sync_columns(self, session: Session) -> None:
        session.add(Config(key="theme", value="dark"))
        session.commit()
        session.expire_all()

        reloaded = session.get(Config, "theme")
        assert reloaded is not None
        assert reloaded.value == "dark"
        assert not hasattr(reloaded, "deleted_at")

    def test_import_batch_round_trips(self, session: Session) -> None:
        account = _make_account(session)
        batch = ImportBatch(
            account=account,
            source_filename="statement.csv",
            row_count=42,
            duplicate_count=5,
        )
        session.add(batch)
        session.commit()
        session.expire_all()

        reloaded = session.get(ImportBatch, batch.id)
        assert reloaded is not None
        assert reloaded.account.name == "Checking"
