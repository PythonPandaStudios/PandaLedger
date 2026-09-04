"""Paycheck estimator screen (PRD §7.8).

Will eventually show real bracket-based federal/state withholding and FICA
estimates per ``IncomeSource``, aggregated across concurrent jobs. Depends
on ``controllers.payroll_controller`` and ``models.payroll``, which are not
built yet.
"""

from __future__ import annotations

import toga

from pandaledger.views.theme import ThemeManager
from pandaledger.views.widgets import section_box


def build_paycheck_view(theme: ThemeManager) -> toga.Box:
    """Build the Paycheck nav section's root widget.

    Args:
        theme: The app's theme manager, for the active color palette.

    Returns:
        A ``toga.Box`` containing the Paycheck screen's current (empty-state)
        content.
    """
    return section_box(
        title="Paycheck",
        empty_state_message=(
            "No income sources yet. Add one from first-run setup to see a "
            "withholding-accurate paycheck estimate here."
        ),
        palette=theme.palette,
    )
