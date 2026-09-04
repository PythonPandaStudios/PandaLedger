"""Budget screen (PRD §7.5, §7.6).

Will eventually show category caps and strategy-driven suggestions
(Rolling Average / 50-30-20 / Zero-Based). Depends on
``controllers.budget_controller`` and the ``models.budgeting`` strategy
modules, which are not built yet.
"""

from __future__ import annotations

import toga

from pandaledger.views.theme import ThemeManager
from pandaledger.views.widgets import section_box


def build_budget_view(theme: ThemeManager) -> toga.Box:
    """Build the Budget nav section's root widget.

    Args:
        theme: The app's theme manager, for the active color palette.

    Returns:
        A ``toga.Box`` containing the Budget screen's current (empty-state)
        content.
    """
    return section_box(
        title="Budget",
        empty_state_message=(
            "No budget plan yet. Pick a budgeting strategy during first-run "
            "setup to see category caps and suggestions here."
        ),
        palette=theme.palette,
    )
