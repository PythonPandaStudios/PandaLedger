"""First-run wizard step 1: create the first Account (PRD §7.1)."""

from __future__ import annotations

from dataclasses import dataclass

import toga
from toga.style import Pack
from travertino.constants import COLUMN

from pandaledger.models.schema import AccountType, InstitutionKind
from pandaledger.views.theme import Palette
from pandaledger.views.widgets import labeled_field, parse_dollars_to_cents, selected_label

#: Selection labels, in display order, mapped to the enum member they mean.
_INSTITUTION_KIND_LABELS: dict[InstitutionKind, str] = {
    InstitutionKind.BANK: "Bank",
    InstitutionKind.CREDIT_UNION: "Credit Union",
    InstitutionKind.BROKER: "Broker",
}
_ACCOUNT_TYPE_LABELS: dict[AccountType, str] = {
    AccountType.CHECKING: "Checking",
    AccountType.SAVINGS: "Savings",
    AccountType.CREDIT: "Credit",
}


@dataclass(frozen=True)
class AccountStepResult:
    """The validated data this step collects.

    Attributes:
        institution_name: Name of the bank/credit union/broker.
        institution_kind: What kind of institution it is.
        account_name: A name for the account.
        account_type: What kind of account it is.
        current_balance_cents: The account's starting balance, in cents.
    """

    institution_name: str
    institution_kind: InstitutionKind
    account_name: str
    account_type: AccountType
    current_balance_cents: int


class AccountStep:
    """Wizard step: name a bank and add the first account at it."""

    title = "Add Your First Account"

    def __init__(self) -> None:
        """Create the step's input widgets."""
        self._institution_name_input = toga.TextInput(placeholder="e.g. Capital One")
        self._institution_kind_selection = toga.Selection(
            items=list(_INSTITUTION_KIND_LABELS.values())
        )
        self._account_name_input = toga.TextInput(placeholder="e.g. Checking")
        self._account_type_selection = toga.Selection(items=list(_ACCOUNT_TYPE_LABELS.values()))
        self._balance_input = toga.TextInput(placeholder="0.00")

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
            "Every budget starts with an account. You can add more later from Import.",
            style=Pack(color=palette.text_muted, margin_bottom=12),
        )
        return toga.Box(
            children=[
                heading,
                description,
                labeled_field("Institution name", self._institution_name_input, palette),
                labeled_field("Institution type", self._institution_kind_selection, palette),
                labeled_field("Account name", self._account_name_input, palette),
                labeled_field("Account type", self._account_type_selection, palette),
                labeled_field("Starting balance ($)", self._balance_input, palette),
            ],
            style=Pack(direction=COLUMN),
        )

    def validate(self) -> str | None:
        """Check the current field values.

        Returns:
            A user-facing error message if something's invalid, else
            ``None``.
        """
        if not (self._institution_name_input.value or "").strip():
            return "Enter your bank or institution's name."
        if not (self._account_name_input.value or "").strip():
            return "Enter a name for this account."
        try:
            parse_dollars_to_cents(self._balance_input.value or "0")
        except ValueError:
            return "Enter a valid starting balance, e.g. 1234.56."
        return None

    @property
    def result(self) -> AccountStepResult:
        """The validated data this step collected.

        Must only be read after :meth:`validate` has returned ``None``.

        Returns:
            The collected :class:`AccountStepResult`.
        """
        reverse_institution_kind = {v: k for k, v in _INSTITUTION_KIND_LABELS.items()}
        reverse_account_type = {v: k for k, v in _ACCOUNT_TYPE_LABELS.items()}
        return AccountStepResult(
            institution_name=(self._institution_name_input.value or "").strip(),
            institution_kind=reverse_institution_kind[
                selected_label(self._institution_kind_selection)
            ],
            account_name=(self._account_name_input.value or "").strip(),
            account_type=reverse_account_type[selected_label(self._account_type_selection)],
            current_balance_cents=parse_dollars_to_cents(self._balance_input.value or "0"),
        )
