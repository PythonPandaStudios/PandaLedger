"""Unit tests for the wizard's Budget Strategy step."""

from __future__ import annotations

from pandaledger.models.schema import BudgetStrategy
from pandaledger.views.theme import LIGHT_PALETTE
from pandaledger.views.wizard.budget_strategy_step import BudgetStrategyStep


def test_defaults_to_rolling_average() -> None:
    step = BudgetStrategyStep()
    step.build(LIGHT_PALETTE)

    assert step.result is BudgetStrategy.ROLLING_AVERAGE


def test_validate_always_passes() -> None:
    """A Selection always has some value once built, so nothing can be invalid."""
    step = BudgetStrategyStep()
    step.build(LIGHT_PALETTE)

    assert step.validate() is None


def test_selecting_zero_based_updates_the_result() -> None:
    step = BudgetStrategyStep()
    step.build(LIGHT_PALETTE)

    step._selection.value = "Zero-Based"

    assert step.result is BudgetStrategy.ZERO_BASED


def test_description_updates_when_selection_changes() -> None:
    step = BudgetStrategyStep()
    step.build(LIGHT_PALETTE)
    initial_description = step._description_label.text

    step._selection.value = "50/30/20 Rule"

    assert step._description_label.text != initial_description
    assert "Needs" in step._description_label.text
