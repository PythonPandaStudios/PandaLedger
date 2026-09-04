"""Statement import screen (PRD §7.2).

Will eventually offer file selection, column mapping, and a post-import
summary for CSV/QFX/QBO statements. Depends on
``controllers.import_controller`` and ``importers.*``, which are not built
yet.
"""

from __future__ import annotations

import toga

from pandaledger.views.widgets import section_box


def build_import_view() -> toga.Box:
    """Build the Import nav section's root widget.

    Returns:
        A ``toga.Box`` containing the Import screen's current (empty-state)
        content.
    """
    return section_box(
        title="Import",
        empty_state_message=(
            "No accounts to import into yet. Add an account first, then "
            "import a CSV, QFX, or QBO statement here."
        ),
    )
