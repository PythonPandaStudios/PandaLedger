"""Savings screen (PRD §7.7).

Will eventually show strategy-driven savings recommendations
(Pay-Yourself-First / Emergency Fund / Leftover Sweep) and goal progress.
Depends on ``controllers.savings_controller`` and the ``models.savings``
strategy modules, which are not built yet.
"""

from __future__ import annotations

import toga

from pandaledger.views.widgets import section_box


def build_savings_view() -> toga.Box:
    """Build the Savings nav section's root widget.

    Returns:
        A ``toga.Box`` containing the Savings screen's current (empty-state)
        content.
    """
    return section_box(
        title="Savings",
        empty_state_message=(
            "No savings goal yet. Pick a savings strategy during first-run "
            "setup to see recommendations and progress here."
        ),
    )
