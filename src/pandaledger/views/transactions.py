"""Transactions screen (PRD §7.4).

Will eventually list an account's transactions with full CRUD, split, and
recurring-transaction support. Depends on ``models.schema`` and
``controllers.transaction_controller``, which are not built yet.
"""

from __future__ import annotations

import toga

from pandaledger.views.theme import ThemeManager
from pandaledger.views.widgets import section_box


def build_transactions_view(theme: ThemeManager) -> toga.Box:
    """Build the Transactions nav section's root widget.

    Args:
        theme: The app's theme manager, for the active color palette.

    Returns:
        A ``toga.Box`` containing the Transactions screen's current
        (empty-state) content.
    """
    return section_box(
        title="Transactions",
        empty_state_message=(
            "No transactions yet. Import a statement or add one manually once an account exists."
        ),
        palette=theme.palette,
    )
