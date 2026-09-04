"""Unit tests for the wizard's Savings Strategy step."""

from __future__ import annotations

from pandaledger.models.schema import SavingsStrategy
from pandaledger.views.theme import LIGHT_PALETTE
from pandaledger.views.wizard.savings_strategy_step import SavingsStrategyStep


def test_defaults_to_pay_yourself_first() -> None:
    step = SavingsStrategyStep()
    step.build(LIGHT_PALETTE)

    assert step.result is SavingsStrategy.PAY_YOURSELF_FIRST


def test_validate_always_passes() -> None:
    step = SavingsStrategyStep()
    step.build(LIGHT_PALETTE)

    assert step.validate() is None


def test_selecting_leftover_sweep_updates_the_result() -> None:
    step = SavingsStrategyStep()
    step.build(LIGHT_PALETTE)

    step._selection.value = "Leftover Sweep"

    assert step.result is SavingsStrategy.LEFTOVER_SWEEP


def test_description_updates_when_selection_changes() -> None:
    step = SavingsStrategyStep()
    step.build(LIGHT_PALETTE)
    initial_description = step._description_label.text

    step._selection.value = "Emergency Fund Target"

    assert step._description_label.text != initial_description
    assert "months" in step._description_label.text
