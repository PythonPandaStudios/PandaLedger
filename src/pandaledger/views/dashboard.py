"""Dashboard screen (PRD §7.1).

Will eventually show current-month budget-vs-actual, the next paycheck
estimate, and savings goal progress, with charts hand-drawn on a Toga
``Canvas``. That content depends on the budget/payroll/savings controllers
and models, which are not built yet, so this screen currently renders its
real empty state rather than fabricated chart data.
"""

from __future__ import annotations

import toga

from pandaledger.views.widgets import section_box


def build_dashboard_view() -> toga.Box:
    """Build the Dashboard nav section's root widget.

    Returns:
        A ``toga.Box`` containing the Dashboard's current (empty-state)
        content.
    """
    return section_box(
        title="Dashboard",
        empty_state_message=(
            "No accounts set up yet. Add an account and import a statement "
            "from the Import screen to see your budget, next paycheck "
            "estimate, and savings progress here."
        ),
    )
