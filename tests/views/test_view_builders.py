"""Unit tests for each nav section's view-builder function.

Every builder should return a fresh, non-empty ``toga.Box`` whose first
child is a heading Label matching the section name — this is what
guarantees each nav item actually renders distinct content.
"""

from __future__ import annotations

import pytest
import toga

from pandaledger.views.budget import build_budget_view
from pandaledger.views.dashboard import build_dashboard_view
from pandaledger.views.import_view import build_import_view
from pandaledger.views.paycheck import build_paycheck_view
from pandaledger.views.savings import build_savings_view
from pandaledger.views.settings import build_settings_view
from pandaledger.views.transactions import build_transactions_view

BUILDERS_AND_TITLES: tuple[tuple[object, str], ...] = (
    (build_dashboard_view, "Dashboard"),
    (build_transactions_view, "Transactions"),
    (build_budget_view, "Budget"),
    (build_savings_view, "Savings"),
    (build_paycheck_view, "Paycheck"),
    (build_import_view, "Import"),
    (build_settings_view, "Settings"),
)


@pytest.mark.parametrize("builder, expected_title", BUILDERS_AND_TITLES)
def test_builder_returns_box_with_matching_heading(builder: object, expected_title: str) -> None:
    """Each builder returns a Box whose heading Label matches its section."""
    box = builder()  # type: ignore[operator]

    assert isinstance(box, toga.Box)
    assert len(box.children) >= 1
    heading = box.children[0]
    assert isinstance(heading, toga.Label)
    assert heading.text == expected_title


@pytest.mark.parametrize("builder, _", BUILDERS_AND_TITLES)
def test_builder_returns_a_fresh_instance_each_call(builder: object, _: str) -> None:
    """Each call returns a distinct Box, since a Toga widget can only have one parent."""
    first = builder()  # type: ignore[operator]
    second = builder()  # type: ignore[operator]

    assert first is not second
