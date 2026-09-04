"""Settings screen (PRD §7.1, §7.8).

Will eventually hold theme selection, strategy changes, tax-table
management, and state-bracket editing. Depends on ``models.database`` and
several controllers that are not built yet.
"""

from __future__ import annotations

import toga

from pandaledger.views.widgets import section_box


def build_settings_view() -> toga.Box:
    """Build the Settings nav section's root widget.

    Returns:
        A ``toga.Box`` containing the Settings screen's current (empty-state)
        content.
    """
    return section_box(
        title="Settings",
        empty_state_message=(
            "Theme, budget/savings strategy, and tax table management will live here."
        ),
    )
