"""First-run wizard step 4: optionally set up the first IncomeSource (PRD §7.1, §7.8)."""

from __future__ import annotations

from dataclasses import dataclass

import toga
from toga.style import Pack
from travertino.constants import COLUMN

from pandaledger.models.schema import FilingStatus, IncomeType, PayScheduleType
from pandaledger.views.theme import Palette
from pandaledger.views.widgets import labeled_field, parse_dollars_to_cents, selected_label

_INCOME_TYPE_LABELS: dict[IncomeType, str] = {
    IncomeType.SALARY: "Salary",
    IncomeType.HOURLY: "Hourly",
}
_SCHEDULE_LABELS: dict[PayScheduleType, str] = {
    PayScheduleType.WEEKLY: "Weekly",
    PayScheduleType.BIWEEKLY: "Biweekly",
    PayScheduleType.SEMI_MONTHLY: "Semi-monthly",
    PayScheduleType.MONTHLY: "Monthly",
}
_FILING_STATUS_LABELS: dict[FilingStatus, str] = {
    FilingStatus.SINGLE: "Single",
    FilingStatus.MARRIED_FILING_JOINTLY: "Married Filing Jointly",
    FilingStatus.MARRIED_FILING_SEPARATELY: "Married Filing Separately",
    FilingStatus.HEAD_OF_HOUSEHOLD: "Head of Household",
}


@dataclass(frozen=True)
class IncomeSourceStepResult:
    """The validated data this step collects.

    Attributes:
        name: A name for the income source (e.g. an employer name).
        income_type: Whether pay is hourly or salaried.
        rate_cents: The hourly rate or salary, in cents.
        schedule: How often this income source pays out.
        filing_status: Federal tax filing status.
        state_code: Two-letter USPS state code.
    """

    name: str
    income_type: IncomeType
    rate_cents: int
    schedule: PayScheduleType
    filing_status: FilingStatus
    state_code: str


class IncomeSourceStep:
    """Wizard step: optionally add the first income source.

    The only optional step in the wizard (PRD §7.1) — a ``Switch`` toggles
    whether the form fields are shown and required.
    """

    title = "Set Up Your First Paycheck (Optional)"

    def __init__(self) -> None:
        """Create the step's toggle and input widgets."""
        self._enabled_switch = toga.Switch("Set up an income source now", on_change=self._on_toggle)
        self._name_input = toga.TextInput(placeholder="e.g. Commdex")
        self._income_type_selection = toga.Selection(items=list(_INCOME_TYPE_LABELS.values()))
        self._rate_input = toga.TextInput(placeholder="0.00")
        self._schedule_selection = toga.Selection(items=list(_SCHEDULE_LABELS.values()))
        self._filing_status_selection = toga.Selection(items=list(_FILING_STATUS_LABELS.values()))
        self._state_code_input = toga.TextInput(placeholder="e.g. CO")
        self._container: toga.Box | None = None
        self._fields_box: toga.Box | None = None
        self._fields_attached = False

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
            "You can skip this and add income sources later from Paycheck.",
            style=Pack(color=palette.text_muted, margin_bottom=12),
        )
        self._fields_box = toga.Box(
            children=[
                labeled_field("Name", self._name_input, palette),
                labeled_field("Pay type", self._income_type_selection, palette),
                labeled_field("Rate ($)", self._rate_input, palette),
                labeled_field("Pay schedule", self._schedule_selection, palette),
                labeled_field("Filing status", self._filing_status_selection, palette),
                labeled_field("State", self._state_code_input, palette),
            ],
            style=Pack(direction=COLUMN),
        )
        self._container = toga.Box(
            children=[heading, description, self._enabled_switch],
            style=Pack(direction=COLUMN),
        )
        # Attached/detached structurally rather than toggled via Pack's
        # `visibility` style: toga-gtk doesn't implement that property at
        # all (confirmed empirically, not just untested) — the fields
        # stayed visible regardless of the switch on a real window.
        # Structural add()/remove() has no such backend gap.
        self._fields_attached = False
        if self._enabled_switch.value:
            self._container.add(self._fields_box)
            self._fields_attached = True
        return self._container

    def validate(self) -> str | None:
        """Check the current field values, if this step is enabled.

        Returns:
            A user-facing error message if something's invalid, else
            ``None``. Always ``None`` when the "set up now" switch is off.
        """
        if not self._enabled_switch.value:
            return None
        if not (self._name_input.value or "").strip():
            return "Enter a name for this income source, or turn off setup for now."
        try:
            rate_cents = parse_dollars_to_cents(self._rate_input.value or "")
        except ValueError:
            return "Enter a valid rate, e.g. 65000 for an annual salary."
        if rate_cents <= 0:
            return "Rate must be greater than zero."
        state_code = (self._state_code_input.value or "").strip()
        if len(state_code) != 2:
            return "Enter a two-letter state code, e.g. CO."
        return None

    @property
    def result(self) -> IncomeSourceStepResult | None:
        """The validated data this step collected, or ``None`` if skipped.

        Must only be read after :meth:`validate` has returned ``None``.

        Returns:
            The collected :class:`IncomeSourceStepResult`, or ``None`` if
            the user left "set up an income source now" off.
        """
        if not self._enabled_switch.value:
            return None
        reverse_income_type = {v: k for k, v in _INCOME_TYPE_LABELS.items()}
        reverse_schedule = {v: k for k, v in _SCHEDULE_LABELS.items()}
        reverse_filing_status = {v: k for k, v in _FILING_STATUS_LABELS.items()}
        return IncomeSourceStepResult(
            name=(self._name_input.value or "").strip(),
            income_type=reverse_income_type[selected_label(self._income_type_selection)],
            rate_cents=parse_dollars_to_cents(self._rate_input.value or "0"),
            schedule=reverse_schedule[selected_label(self._schedule_selection)],
            filing_status=reverse_filing_status[selected_label(self._filing_status_selection)],
            state_code=(self._state_code_input.value or "").strip().upper(),
        )

    def _on_toggle(self, widget: toga.Switch) -> None:
        """Attach or detach the income-source fields to match the switch.

        Args:
            widget: The switch that changed (unused; the current value is
                read from ``self._enabled_switch`` instead).
        """
        if self._container is None or self._fields_box is None:
            return
        if self._enabled_switch.value and not self._fields_attached:
            self._container.add(self._fields_box)
            self._fields_attached = True
        elif not self._enabled_switch.value and self._fields_attached:
            self._container.remove(self._fields_box)
            self._fields_attached = False
