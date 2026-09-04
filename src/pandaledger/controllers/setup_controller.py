"""First-run setup logic (PRD §7.1 wizard).

Not one of the controllers named in PRD §5's illustrative architecture
tree, but that list is explicitly "one module per feature area," and
first-run setup — creating the first Account, picking a budget/savings
strategy, optionally adding an IncomeSource — is its own feature area, so
it gets its own controller rather than being wedged into
``budget_controller``/``savings_controller``, which don't exist yet
either and are meant to own the *ongoing* strategy logic (PRD §7.5,
§7.7), not account creation.

Budget/savings strategy choices are written to :class:`~pandaledger.models.schema.Config`
rather than an immediate `BudgetPlan`/`SavingsGoal` row: PRD §7.5/§7.7
describe the strategy as "a first-run choice, changeable anytime," and
`Config`'s own PRD §6 description — "theme, active strategy IDs, etc." —
is exactly this. A concrete `BudgetPlan` is month-scoped and a
`SavingsGoal` needs real spending history to size a sensible target,
neither of which exist at first run.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from pandaledger.models.schema import (
    Account,
    AccountType,
    BudgetStrategy,
    Config,
    FilingStatus,
    IncomeSource,
    IncomeType,
    Institution,
    InstitutionKind,
    PayScheduleType,
    SavingsStrategy,
)

#: Config key the active budget strategy is stored under.
BUDGET_STRATEGY_CONFIG_KEY = "budget_strategy"

#: Config key the active savings strategy is stored under.
SAVINGS_STRATEGY_CONFIG_KEY = "savings_strategy"


def has_completed_first_run(session: Session) -> bool:
    """Check whether first-run setup has already happened.

    Presence of any non-deleted :class:`Account` is used as the signal —
    the wizard's mandatory first step is creating one, so its existence
    means the wizard has run.

    Args:
        session: The database session to query with.

    Returns:
        ``True`` if at least one account exists, ``False`` if this is a
        fresh install that should see the first-run wizard.
    """
    statement = select(Account.id).where(Account.deleted_at.is_(None)).limit(1)
    return session.execute(statement).first() is not None


def create_first_account(
    session: Session,
    *,
    institution_name: str,
    institution_kind: InstitutionKind,
    account_name: str,
    account_type: AccountType,
    current_balance_cents: int,
) -> Account:
    """Create the Institution + Account the wizard's first step collects.

    Args:
        session: The database session to persist through.
        institution_name: Name of the bank/credit union/broker.
        institution_kind: What kind of institution it is.
        account_name: A name for the account (e.g. "Checking").
        account_type: What kind of account it is.
        current_balance_cents: The account's starting balance, in cents.
            May be negative (an overdrawn/credit balance) or zero.

    Returns:
        The newly created, already-flushed ``Account``.

    Raises:
        ValueError: If ``institution_name`` or ``account_name`` is blank.
    """
    if not institution_name.strip():
        raise ValueError("institution_name must not be blank")
    if not account_name.strip():
        raise ValueError("account_name must not be blank")

    institution = Institution(name=institution_name.strip(), kind=institution_kind)
    account = Account(
        institution=institution,
        name=account_name.strip(),
        type=account_type,
        current_balance_cents=current_balance_cents,
    )
    session.add(account)
    session.flush()
    return account


def set_budget_strategy(session: Session, strategy: BudgetStrategy) -> None:
    """Record the user's chosen budget strategy in :class:`Config`.

    Args:
        session: The database session to persist through.
        strategy: The strategy chosen in the wizard (PRD §7.5).
    """
    _upsert_config(session, BUDGET_STRATEGY_CONFIG_KEY, strategy.value)


def set_savings_strategy(session: Session, strategy: SavingsStrategy) -> None:
    """Record the user's chosen savings strategy in :class:`Config`.

    Args:
        session: The database session to persist through.
        strategy: The strategy chosen in the wizard (PRD §7.7).
    """
    _upsert_config(session, SAVINGS_STRATEGY_CONFIG_KEY, strategy.value)


def create_income_source(
    session: Session,
    *,
    name: str,
    income_type: IncomeType,
    rate_cents: int,
    schedule: PayScheduleType,
    filing_status: FilingStatus,
    state_code: str,
) -> IncomeSource:
    """Create the optional IncomeSource the wizard's last step collects.

    Args:
        session: The database session to persist through.
        name: A name for the income source (e.g. an employer name).
        income_type: Whether pay is hourly or salaried.
        rate_cents: The hourly rate or salary, in cents. Must be positive.
        schedule: How often this income source pays out.
        filing_status: Federal tax filing status, for the payroll engine
            (PRD §7.8).
        state_code: Two-letter USPS state code, for state withholding.

    Returns:
        The newly created, already-flushed ``IncomeSource``.

    Raises:
        ValueError: If ``name`` is blank, ``rate_cents`` isn't positive,
            or ``state_code`` isn't a two-letter code.
    """
    if not name.strip():
        raise ValueError("name must not be blank")
    if rate_cents <= 0:
        raise ValueError("rate_cents must be positive")
    normalized_state_code = state_code.strip().upper()
    if len(normalized_state_code) != 2:
        raise ValueError("state_code must be a two-letter USPS state code")

    income_source = IncomeSource(
        name=name.strip(),
        income_type=income_type,
        rate_cents=rate_cents,
        schedule=schedule,
        filing_status=filing_status,
        state_code=normalized_state_code,
    )
    session.add(income_source)
    session.flush()
    return income_source


def _upsert_config(session: Session, key: str, value: str) -> None:
    """Set a :class:`Config` row's value, creating it if it doesn't exist yet.

    Args:
        session: The database session to persist through.
        key: The config key.
        value: The value to store.
    """
    existing = session.get(Config, key)
    if existing is not None:
        existing.value = value
    else:
        session.add(Config(key=key, value=value))
    session.flush()
