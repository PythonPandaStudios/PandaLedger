"""SQLAlchemy 2.x declarative schema (PRD §6).

Pure data model — no Toga imports here (see ``CLAUDE.md``: ``models/`` and
``importers/`` stay Toga-free so business logic is testable headlessly).

Money is always stored as integer cents, never ``float`` (PRD §6): a
budgeting/payroll app that silently accumulates floating-point rounding
error is a correctness bug, not a rounding curiosity.

Every table gets a UUID string primary key, an ``updated_at`` timestamp,
and soft deletes (``deleted_at``), per PRD §6 — this is forward-looking
for the v2 sync design (§9.2), where a delete on one device must not be
"resurrected" by a concurrent update racing in from another, and
``updated_at`` is what makes last-write-wins possible at all. Retrofitting
this later would mean a painful migration, so it's in from the start. The
one exception is ``Config``, which PRD §6 explicitly describes as "kept
as-is" — a plain settings key/value table, not a syncable entity.
"""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _new_uuid() -> str:
    """Generate a new primary-key value.

    Returns:
        A freshly generated UUID4, in standard hyphenated string form.
    """
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    """Return the current time in UTC, as a naive ``datetime``.

    Used as both the ``default`` and ``onupdate`` for every table's
    ``updated_at`` column, so it reflects insert time until the first
    update, then every update after that.

    Deliberately naive rather than timezone-aware: SQLite has no native
    timestamp-with-timezone type, and silently drops the offset on
    round-trip even when the column is declared ``DateTime(timezone=True)``
    — a value written as ``...+00:00`` comes back with ``tzinfo=None``. A
    naive-but-always-UTC convention avoids that trap entirely, rather than
    comparing a freshly-created aware value against a round-tripped naive
    one and raising ``TypeError``.

    Returns:
        The current time in UTC, with no ``tzinfo`` attached.
    """
    return datetime.now(UTC).replace(tzinfo=None)


class Base(DeclarativeBase):
    """Declarative base for all PandaLedger ORM models."""


class SyncedMixin:
    """Adds the uuid/updated_at/soft-delete columns PRD §6 requires on every table.

    Attributes:
        id: UUID primary key, generated client-side so it's stable before
            the row is ever flushed to the database (needed for the
            journaled-change sync design in PRD §9.2).
        updated_at: When this row was last inserted or updated.
        deleted_at: When this row was soft-deleted, or ``None`` if it
            hasn't been. Rows are never hard-deleted so a delete on one
            device can't be "resurrected" by a concurrent update from
            another once sync (§9.2) exists.
    """

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    updated_at: Mapped[datetime] = mapped_column(default=_utcnow, onupdate=_utcnow, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)


class InstitutionKind(str, enum.Enum):
    """What kind of financial institution an :class:`Institution` is."""

    BANK = "bank"
    CREDIT_UNION = "credit_union"
    BROKER = "broker"


class AccountType(str, enum.Enum):
    """What kind of account an :class:`Account` is."""

    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"


class FileFormat(str, enum.Enum):
    """Statement file formats supported for import (PRD §7.2)."""

    CSV = "csv"
    QFX = "qfx"
    QBO = "qbo"


class CategoryType(str, enum.Enum):
    """A :class:`Category`'s role in the 50/30/20 budget strategy (PRD §7.5)."""

    FIXED = "Fixed"
    VARIABLE = "Variable"
    SAVINGS = "Savings"


class MatchType(str, enum.Enum):
    """How a :class:`CategorizationRule` matches a transaction's payee."""

    SUBSTRING = "substring"
    REGEX = "regex"


class RecurrenceFrequency(str, enum.Enum):
    """How often a :class:`RecurringTransaction` recurs.

    PRD §7.4 gives "weekly/biweekly/monthly/etc." — quarterly and annually
    are added here since "etc." is explicitly open-ended and both are
    common real-world bill frequencies (insurance premiums, subscriptions)
    that a recurring-transaction feature needs to cover.
    """

    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    SEMI_MONTHLY = "semi_monthly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class IncomeType(str, enum.Enum):
    """How an :class:`IncomeSource`'s pay rate is structured."""

    HOURLY = "hourly"
    SALARY = "salary"


class PayScheduleType(str, enum.Enum):
    """How often an :class:`IncomeSource` pays out."""

    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    SEMI_MONTHLY = "semi_monthly"
    MONTHLY = "monthly"


class FilingStatus(str, enum.Enum):
    """Federal tax filing status, used by the payroll engine (PRD §7.8).

    ``head_of_household`` isn't named explicitly in PRD §7.8's Additional
    Medicare Tax thresholds (single/MFJ/MFS only), but it's a standard IRS
    Pub 15-T filing status the federal bracket tables will need too, so
    it's included here for schema completeness.
    """

    SINGLE = "single"
    MARRIED_FILING_JOINTLY = "married_filing_jointly"
    MARRIED_FILING_SEPARATELY = "married_filing_separately"
    HEAD_OF_HOUSEHOLD = "head_of_household"


class DeductionCategory(str, enum.Enum):
    """What kind of payroll deduction a :class:`Deduction` is."""

    RETIREMENT_401K = "401k"
    HSA = "hsa"
    INSURANCE = "insurance"
    ROTH = "roth"
    OTHER = "other"


class BudgetStrategy(str, enum.Enum):
    """Budget suggestion strategies offered at first-run setup (PRD §7.5)."""

    ZERO_BASED = "zero_based"
    FIFTY_THIRTY_TWENTY = "fifty_thirty_twenty"
    ROLLING_AVERAGE = "rolling_average"


class SavingsStrategy(str, enum.Enum):
    """Savings recommendation strategies offered at first-run setup (PRD §7.7)."""

    PAY_YOURSELF_FIRST = "pay_yourself_first"
    EMERGENCY_FUND = "emergency_fund"
    LEFTOVER_SWEEP = "leftover_sweep"


class Institution(Base, SyncedMixin):
    """A bank, credit union, or broker an :class:`Account` belongs to."""

    __tablename__ = "institutions"

    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[InstitutionKind] = mapped_column(SAEnum(InstitutionKind))
    notes: Mapped[str | None] = mapped_column(default=None)

    accounts: Mapped[list[Account]] = relationship(back_populates="institution")
    import_column_maps: Mapped[list[ImportColumnMap]] = relationship(back_populates="institution")


class ImportColumnMap(Base, SyncedMixin):
    """A saved source-column → field mapping for statement imports (PRD §7.2).

    ``institution_id`` is nullable to allow a generic, institution-agnostic
    mapping (e.g. a common CSV export shape shared by several banks).
    """

    __tablename__ = "import_column_maps"

    institution_id: Mapped[str | None] = mapped_column(ForeignKey("institutions.id"), default=None)
    file_format: Mapped[FileFormat] = mapped_column(SAEnum(FileFormat))
    column_mapping: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    institution: Mapped[Institution | None] = relationship(back_populates="import_column_maps")
    accounts: Mapped[list[Account]] = relationship(back_populates="import_column_map")


class Account(Base, SyncedMixin):
    """A checking/savings/credit account at an :class:`Institution`."""

    __tablename__ = "accounts"

    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"))
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[AccountType] = mapped_column(SAEnum(AccountType))
    current_balance_cents: Mapped[int] = mapped_column(default=0)
    import_column_map_id: Mapped[str | None] = mapped_column(
        ForeignKey("import_column_maps.id"), default=None
    )

    institution: Mapped[Institution] = relationship(back_populates="accounts")
    import_column_map: Mapped[ImportColumnMap | None] = relationship(back_populates="accounts")
    import_batches: Mapped[list[ImportBatch]] = relationship(back_populates="account")
    transactions: Mapped[list[Transaction]] = relationship(back_populates="account")
    recurring_transactions: Mapped[list[RecurringTransaction]] = relationship(
        back_populates="account"
    )


class ImportBatch(Base, SyncedMixin):
    """One statement-import run, for the post-import summary screen (PRD §7.2)."""

    __tablename__ = "import_batches"

    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))
    imported_at: Mapped[datetime] = mapped_column(default=_utcnow)
    source_filename: Mapped[str] = mapped_column(String(500))
    row_count: Mapped[int] = mapped_column(default=0)
    duplicate_count: Mapped[int] = mapped_column(default=0)

    account: Mapped[Account] = relationship(back_populates="import_batches")
    transactions: Mapped[list[Transaction]] = relationship(back_populates="import_batch")


class Category(Base, SyncedMixin):
    """A spending/savings category, usable in both budgeting and categorization rules."""

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[CategoryType] = mapped_column(SAEnum(CategoryType))
    user_created: Mapped[bool] = mapped_column(default=True)
    monthly_limit_cents: Mapped[int | None] = mapped_column(default=None)
    parent_category_id: Mapped[str | None] = mapped_column(
        ForeignKey("categories.id"), default=None
    )

    parent: Mapped[Category | None] = relationship(
        remote_side="Category.id", back_populates="children"
    )
    children: Mapped[list[Category]] = relationship(back_populates="parent")
    rules: Mapped[list[CategorizationRule]] = relationship(back_populates="category")
    transactions: Mapped[list[Transaction]] = relationship(back_populates="category")
    recurring_transactions: Mapped[list[RecurringTransaction]] = relationship(
        back_populates="category"
    )
    budget_lines: Mapped[list[BudgetLine]] = relationship(back_populates="category")


class CategorizationRule(Base, SyncedMixin):
    """A payee-pattern → category auto-categorization rule (PRD §7.3)."""

    __tablename__ = "categorization_rules"

    pattern: Mapped[str] = mapped_column(String(500))
    match_type: Mapped[MatchType] = mapped_column(SAEnum(MatchType))
    category_id: Mapped[str] = mapped_column(ForeignKey("categories.id"))
    priority: Mapped[int] = mapped_column(default=100)
    auto_apply: Mapped[bool] = mapped_column(default=False)
    created_from_transaction_id: Mapped[str | None] = mapped_column(
        ForeignKey("transactions.id"), default=None
    )

    category: Mapped[Category] = relationship(back_populates="rules")
    created_from_transaction: Mapped[Transaction | None] = relationship(
        foreign_keys=[created_from_transaction_id]
    )


class Transaction(Base, SyncedMixin):
    """A single ledger line: imported, manual, or one side of a split (PRD §7.2, §7.4).

    ``dedupe_hash`` is unique per account (PRD §7.2): re-importing the same
    statement, or an overlapping date range from a second export, must be
    a no-op rather than create duplicate rows. QFX/QBO imports use the
    bank-assigned FITID as ``external_txn_id`` when available — a much
    more reliable dedupe key than any hash — falling back to
    ``dedupe_hash`` (a hash of account/date/amount/payee) for CSV, which
    carries no such ID.
    """

    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("account_id", "dedupe_hash", name="uq_transaction_account_dedupe_hash"),
    )

    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))
    date: Mapped[date] = mapped_column()
    payee: Mapped[str] = mapped_column(String(300))
    amount_cents: Mapped[int] = mapped_column()
    notes: Mapped[str | None] = mapped_column(default=None)
    category_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id"), default=None)
    import_batch_id: Mapped[str | None] = mapped_column(
        ForeignKey("import_batches.id"), default=None
    )
    dedupe_hash: Mapped[str] = mapped_column(String(64))
    external_txn_id: Mapped[str | None] = mapped_column(String(100), default=None)
    parent_transaction_id: Mapped[str | None] = mapped_column(
        ForeignKey("transactions.id"), default=None
    )
    is_pending_review: Mapped[bool] = mapped_column(default=False)

    account: Mapped[Account] = relationship(back_populates="transactions")
    category: Mapped[Category | None] = relationship(back_populates="transactions")
    import_batch: Mapped[ImportBatch | None] = relationship(back_populates="transactions")
    parent: Mapped[Transaction | None] = relationship(
        remote_side="Transaction.id",
        back_populates="children",
        foreign_keys=[parent_transaction_id],
    )
    children: Mapped[list[Transaction]] = relationship(
        back_populates="parent", foreign_keys=[parent_transaction_id]
    )


class RecurringTransaction(Base, SyncedMixin):
    """A projected, repeating transaction (PRD §7.4).

    Generates a projected :class:`Transaction` on ``next_due_date`` for
    forward-looking budget math, then reconciles with the real imported
    transaction when it shows up rather than double-counting it.
    """

    __tablename__ = "recurring_transactions"

    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))
    category_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id"), default=None)
    payee: Mapped[str] = mapped_column(String(300))
    amount_cents: Mapped[int] = mapped_column()
    frequency: Mapped[RecurrenceFrequency] = mapped_column(SAEnum(RecurrenceFrequency))
    next_due_date: Mapped[date] = mapped_column()
    last_generated_date: Mapped[date | None] = mapped_column(default=None)

    account: Mapped[Account] = relationship(back_populates="recurring_transactions")
    category: Mapped[Category | None] = relationship(back_populates="recurring_transactions")


class IncomeSource(Base, SyncedMixin):
    """One job/income stream, with its own independent payroll withholding (PRD §7.8)."""

    __tablename__ = "income_sources"

    name: Mapped[str] = mapped_column(String(200))
    income_type: Mapped[IncomeType] = mapped_column(SAEnum(IncomeType))
    rate_cents: Mapped[int] = mapped_column()
    schedule: Mapped[PayScheduleType] = mapped_column(SAEnum(PayScheduleType))
    schedule_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    filing_status: Mapped[FilingStatus] = mapped_column(SAEnum(FilingStatus))
    state_code: Mapped[str] = mapped_column(String(2))

    deductions: Mapped[list[Deduction]] = relationship(back_populates="income_source")


class Deduction(Base, SyncedMixin):
    """A pre- or post-tax payroll deduction on an :class:`IncomeSource` (PRD §7.8).

    ``amount_cents_or_percent`` holds a cents amount when ``is_percent`` is
    ``False``. When ``is_percent`` is ``True``, it instead holds the
    percentage in basis points (hundredths of a percent — e.g. 525 means
    5.25%), so a percent-based deduction (a common 401k election) never
    needs a ``float`` either.
    """

    __tablename__ = "deductions"

    income_source_id: Mapped[str] = mapped_column(ForeignKey("income_sources.id"))
    name: Mapped[str] = mapped_column(String(200))
    amount_cents_or_percent: Mapped[int] = mapped_column()
    is_percent: Mapped[bool] = mapped_column(default=False)
    is_pre_tax: Mapped[bool] = mapped_column(default=True)
    category: Mapped[DeductionCategory] = mapped_column(SAEnum(DeductionCategory))

    income_source: Mapped[IncomeSource] = relationship(back_populates="deductions")


class BudgetPlan(Base, SyncedMixin):
    """A month's strategy-driven budget (PRD §7.5, §7.6)."""

    __tablename__ = "budget_plans"

    month: Mapped[int] = mapped_column()
    year: Mapped[int] = mapped_column()
    strategy: Mapped[BudgetStrategy] = mapped_column(SAEnum(BudgetStrategy))
    strategy_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    lines: Mapped[list[BudgetLine]] = relationship(back_populates="budget_plan")


class BudgetLine(Base, SyncedMixin):
    """One category's cap within a :class:`BudgetPlan` (PRD §7.6).

    ``suggested_cents`` is machine-generated by whichever strategy is
    active; ``approved_cents`` is what the user actually commits to
    (defaults to the suggestion, but is user-editable).
    """

    __tablename__ = "budget_lines"

    budget_plan_id: Mapped[str] = mapped_column(ForeignKey("budget_plans.id"))
    category_id: Mapped[str] = mapped_column(ForeignKey("categories.id"))
    suggested_cents: Mapped[int] = mapped_column(default=0)
    approved_cents: Mapped[int] = mapped_column(default=0)

    budget_plan: Mapped[BudgetPlan] = relationship(back_populates="lines")
    category: Mapped[Category] = relationship(back_populates="budget_lines")


class SavingsGoal(Base, SyncedMixin):
    """A strategy-driven savings target and its progress (PRD §7.7)."""

    __tablename__ = "savings_goals"

    strategy: Mapped[SavingsStrategy] = mapped_column(SAEnum(SavingsStrategy))
    strategy_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    target_cents: Mapped[int] = mapped_column(default=0)
    current_cents: Mapped[int] = mapped_column(default=0)


class Config(Base):
    """A simple settings key/value row (theme, active strategy IDs, etc.).

    Deliberately excluded from :class:`SyncedMixin` — PRD §6 describes this
    table as "kept as-is," unlike every syncable entity table above it.
    """

    __tablename__ = "config"

    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    value: Mapped[str] = mapped_column()
