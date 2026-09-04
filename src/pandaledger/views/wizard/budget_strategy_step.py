"""First-run wizard step 2: pick a budget strategy (PRD §7.1, §7.5)."""

from __future__ import annotations

import toga
from toga.style import Pack
from travertino.constants import COLUMN

from pandaledger.models.schema import BudgetStrategy
from pandaledger.views.theme import Palette
from pandaledger.views.widgets import selected_label

#: Selection labels, in display order, mapped to the enum member they mean.
_STRATEGY_LABELS: dict[BudgetStrategy, str] = {
    BudgetStrategy.ROLLING_AVERAGE: "Rolling Average",
    BudgetStrategy.FIFTY_THIRTY_TWENTY: "50/30/20 Rule",
    BudgetStrategy.ZERO_BASED: "Zero-Based",
}

#: One-line explanation shown under the selection, per strategy (PRD §7.5).
_STRATEGY_DESCRIPTIONS: dict[BudgetStrategy, str] = {
    BudgetStrategy.ROLLING_AVERAGE: (
        "Each category's suggested cap is your trailing 3-month average "
        "spend in it — a good default if you have import history but no "
        "budgeting experience yet."
    ),
    BudgetStrategy.FIFTY_THIRTY_TWENTY: (
        "Splits net income into Needs, Wants, and Savings using your "
        "categories' Fixed/Variable/Savings types."
    ),
    BudgetStrategy.ZERO_BASED: (
        "Every dollar of the month's income gets assigned to a category "
        "until nothing is left unallocated."
    ),
}


class BudgetStrategyStep:
    """Wizard step: choose the budget-suggestion strategy (changeable later)."""

    title = "Choose a Budget Strategy"

    def __init__(self) -> None:
        """Create the step's selection widget, defaulted to the first strategy."""
        self._selection = toga.Selection(
            items=list(_STRATEGY_LABELS.values()), on_change=self._on_change
        )
        self._description_label = toga.Label("")

    def build(self, palette: Palette) -> toga.Box:
        """Build this step's form.

        Args:
            palette: Active color palette.

        Returns:
            A vertical ``toga.Box`` containing the step's fields.
        """
        heading = toga.Label(
            self.title,
            style=Pack(font_size=18, font_weight="bold", color=palette.text, margin_bottom=4),
        )
        description = toga.Label(
            "You can change this anytime from Settings.",
            style=Pack(color=palette.text_muted, margin_bottom=12),
        )
        self._description_label.style.color = palette.text_muted
        self._description_label.style.margin_top = 8
        self._description_label.text = self._current_description()
        return toga.Box(
            children=[heading, description, self._selection, self._description_label],
            style=Pack(direction=COLUMN),
        )

    def validate(self) -> str | None:
        """Check the current selection.

        Returns:
            Always ``None`` — a ``Selection`` always has a value once
            built, so there's nothing invalid to report.
        """
        return None

    @property
    def result(self) -> BudgetStrategy:
        """The chosen strategy.

        Returns:
            The selected :class:`BudgetStrategy`.
        """
        reverse_labels = {v: k for k, v in _STRATEGY_LABELS.items()}
        return reverse_labels[selected_label(self._selection)]

    def _current_description(self) -> str:
        """Look up the description for the currently selected strategy."""
        reverse_labels = {v: k for k, v in _STRATEGY_LABELS.items()}
        strategy = reverse_labels[selected_label(self._selection)]
        return _STRATEGY_DESCRIPTIONS[strategy]

    def _on_change(self, widget: toga.Selection) -> None:
        """Update the description label to match the newly selected strategy.

        Args:
            widget: The selection widget that changed (unused; the current
                value is read from ``self._selection`` instead).
        """
        self._description_label.text = self._current_description()
