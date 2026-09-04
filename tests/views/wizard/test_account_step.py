"""Unit tests for the wizard's Account step."""

from __future__ import annotations

from pandaledger.models.schema import AccountType, InstitutionKind
from pandaledger.views.theme import LIGHT_PALETTE
from pandaledger.views.wizard.account_step import AccountStep


def test_build_returns_a_box() -> None:
    step = AccountStep()

    box = step.build(LIGHT_PALETTE)

    assert box is not None


def test_validate_requires_institution_name() -> None:
    step = AccountStep()
    step.build(LIGHT_PALETTE)
    step._account_name_input.value = "Checking"

    assert step.validate() is not None


def test_validate_requires_account_name() -> None:
    step = AccountStep()
    step.build(LIGHT_PALETTE)
    step._institution_name_input.value = "Capital One"

    assert step.validate() is not None


def test_validate_rejects_an_unparseable_balance() -> None:
    step = AccountStep()
    step.build(LIGHT_PALETTE)
    step._institution_name_input.value = "Capital One"
    step._account_name_input.value = "Checking"
    step._balance_input.value = "not a number"

    assert step.validate() is not None


def test_validate_passes_with_a_blank_balance_defaulting_to_zero() -> None:
    step = AccountStep()
    step.build(LIGHT_PALETTE)
    step._institution_name_input.value = "Capital One"
    step._account_name_input.value = "Checking"

    assert step.validate() is None
    assert step.result.current_balance_cents == 0


def test_result_reflects_entered_values() -> None:
    step = AccountStep()
    step.build(LIGHT_PALETTE)
    step._institution_name_input.value = "  Capital One  "
    step._institution_kind_selection.value = "Credit Union"
    step._account_name_input.value = "  Savings  "
    step._account_type_selection.value = "Savings"
    step._balance_input.value = "1234.56"

    result = step.result

    assert result.institution_name == "Capital One"
    assert result.institution_kind is InstitutionKind.CREDIT_UNION
    assert result.account_name == "Savings"
    assert result.account_type is AccountType.SAVINGS
    assert result.current_balance_cents == 123_456


def test_negative_balance_is_valid() -> None:
    """An overdrawn starting balance is real, not an error."""
    step = AccountStep()
    step.build(LIGHT_PALETTE)
    step._institution_name_input.value = "Capital One"
    step._account_name_input.value = "Checking"
    step._balance_input.value = "-42.00"

    assert step.validate() is None
    assert step.result.current_balance_cents == -4_200
