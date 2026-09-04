"""Unit tests for the wizard's optional Income Source step."""

from __future__ import annotations

from pandaledger.models.schema import FilingStatus, IncomeType, PayScheduleType
from pandaledger.views.theme import LIGHT_PALETTE
from pandaledger.views.wizard.income_source_step import IncomeSourceStep


def test_skipped_by_default() -> None:
    """The switch starts off, so validate() passes and result() is None untouched."""
    step = IncomeSourceStep()
    step.build(LIGHT_PALETTE)

    assert step.validate() is None
    assert step.result is None


def test_fields_start_detached_from_the_container() -> None:
    """Fields are structurally absent when off, not just styled hidden.

    Pack's `visibility` style isn't implemented by the GTK backend at
    all, so hiding must be structural (not in the parent's children) to
    actually work on a real window.
    """
    step = IncomeSourceStep()
    box = step.build(LIGHT_PALETTE)

    assert step._fields_box is not None
    assert step._fields_box not in box.children


def test_toggling_on_attaches_the_fields() -> None:
    step = IncomeSourceStep()
    box = step.build(LIGHT_PALETTE)

    step._enabled_switch.value = True

    assert step._fields_box is not None
    assert step._fields_box in box.children


def test_toggling_off_again_detaches_the_fields() -> None:
    step = IncomeSourceStep()
    box = step.build(LIGHT_PALETTE)

    step._enabled_switch.value = True
    step._enabled_switch.value = False

    assert step._fields_box is not None
    assert step._fields_box not in box.children


def test_enabled_but_blank_name_is_rejected() -> None:
    step = IncomeSourceStep()
    step.build(LIGHT_PALETTE)
    step._enabled_switch.value = True

    assert step.validate() is not None


def test_enabled_with_bad_rate_is_rejected() -> None:
    step = IncomeSourceStep()
    step.build(LIGHT_PALETTE)
    step._enabled_switch.value = True
    step._name_input.value = "Commdex"
    step._rate_input.value = "not a number"
    step._state_code_input.value = "CO"

    assert step.validate() is not None


def test_enabled_with_zero_rate_is_rejected() -> None:
    step = IncomeSourceStep()
    step.build(LIGHT_PALETTE)
    step._enabled_switch.value = True
    step._name_input.value = "Commdex"
    step._rate_input.value = "0"
    step._state_code_input.value = "CO"

    assert step.validate() is not None


def test_enabled_with_bad_state_code_is_rejected() -> None:
    step = IncomeSourceStep()
    step.build(LIGHT_PALETTE)
    step._enabled_switch.value = True
    step._name_input.value = "Commdex"
    step._rate_input.value = "80000"
    step._state_code_input.value = "Colorado"

    assert step.validate() is not None


def test_valid_enabled_step_produces_a_result() -> None:
    step = IncomeSourceStep()
    step.build(LIGHT_PALETTE)
    step._enabled_switch.value = True
    step._name_input.value = "Commdex"
    step._income_type_selection.value = "Hourly"
    step._rate_input.value = "27.50"
    step._schedule_selection.value = "Weekly"
    step._filing_status_selection.value = "Head of Household"
    step._state_code_input.value = "co"

    assert step.validate() is None
    result = step.result
    assert result is not None
    assert result.name == "Commdex"
    assert result.income_type is IncomeType.HOURLY
    assert result.rate_cents == 2_750
    assert result.schedule is PayScheduleType.WEEKLY
    assert result.filing_status is FilingStatus.HEAD_OF_HOUSEHOLD
    assert result.state_code == "CO"
