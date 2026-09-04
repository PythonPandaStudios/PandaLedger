"""Hand-rolled bar/line chart drawing on a Toga ``Canvas`` (PRD §7.1, §3).

Toga has no built-in charting widget, so the Dashboard's budget-vs-actual,
paycheck, and savings-progress visuals will eventually be drawn here
directly onto a ``toga.Canvas`` — a small, dependency-free chart engine
rather than a bundled charting library. This module only draws whatever
data it's given; it has no knowledge of budgets, paychecks, or savings —
that wiring happens once the corresponding controllers/models exist.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import toga
from toga.constants import Baseline

from pandaledger.views.theme import Palette

#: Fraction of a bar's horizontal slot occupied by the bar itself; the rest
#: is the gap between adjacent bars.
BAR_WIDTH_FRACTION = 0.7

#: Height, in canvas units, reserved at the bottom of the plot area for
#: category/point labels.
LABEL_AREA_HEIGHT = 20.0

#: Vertical gap, in canvas units, between the plot area and its labels.
LABEL_MARGIN = 4.0

#: Side length, in canvas units, of the square marker drawn at each line
#: chart point.
POINT_MARKER_SIZE = 6.0

#: Stroke width, in canvas units, of a line chart's connecting line.
LINE_WIDTH = 2.0


@dataclass(frozen=True)
class BarDatum:
    """One labeled bar in a bar chart.

    Attributes:
        label: Category label drawn below the bar.
        value_cents: The bar's value, as integer cents (PRD §6 — money is
            never a float). Must be zero or positive.
    """

    label: str
    value_cents: int


@dataclass(frozen=True)
class LinePoint:
    """One point on a line chart.

    Attributes:
        label: Label drawn below the point (e.g. a month name).
        value_cents: The point's value, as integer cents. Must be zero or
            positive.
    """

    label: str
    value_cents: int


def draw_bar_chart(
    canvas: toga.Canvas,
    data: Sequence[BarDatum],
    *,
    width: float,
    height: float,
    palette: Palette,
) -> None:
    """Draw a vertical bar chart onto ``canvas``, replacing its contents.

    Args:
        canvas: The Canvas to draw onto.
        data: The bars to plot, left to right, in the given order. An
            empty sequence draws only the baseline.
        width: Width of the drawing area, in the canvas's own coordinate
            units.
        height: Height of the drawing area.
        palette: Active color palette (PRD §7.1 light/dark theme) — bars
            use ``palette.accent``, labels use ``palette.text_muted``, and
            the baseline uses ``palette.border``.

    Raises:
        ValueError: If any datum's ``value_cents`` is negative — this
            engine only plots non-negative amounts (spend, savings
            balances, etc.), not signed deltas.
    """
    if any(datum.value_cents < 0 for datum in data):
        raise ValueError("draw_bar_chart does not support negative values")

    canvas.root_state.drawing_actions.clear()
    canvas.redraw()

    plot_height = max(height - LABEL_AREA_HEIGHT, 0.0)
    if data:
        max_value = max((datum.value_cents for datum in data), default=0) or 1
        slot_width = width / len(data)
        bar_width = slot_width * BAR_WIDTH_FRACTION

        for index, datum in enumerate(data):
            bar_height = (datum.value_cents / max_value) * plot_height
            x = index * slot_width + (slot_width - bar_width) / 2
            y = plot_height - bar_height
            with canvas.fill(color=palette.accent):
                canvas.rect(x, y, bar_width, bar_height)
            _draw_centered_label(
                canvas,
                datum.label,
                center_x=index * slot_width + slot_width / 2,
                top_y=plot_height + LABEL_MARGIN,
                palette=palette,
            )

    _draw_baseline(canvas, width=width, y=plot_height, palette=palette)


def draw_line_chart(
    canvas: toga.Canvas,
    points: Sequence[LinePoint],
    *,
    width: float,
    height: float,
    palette: Palette,
) -> None:
    """Draw a line chart onto ``canvas``, replacing its contents.

    Args:
        canvas: The Canvas to draw onto.
        points: The points to plot, left to right, in the given order. An
            empty sequence draws only the baseline; a single point draws
            just its marker and label (no line has a slope with one
            point).
        width: Width of the drawing area, in the canvas's own coordinate
            units.
        height: Height of the drawing area.
        palette: Active color palette (PRD §7.1 light/dark theme) — the
            line and point markers use ``palette.accent``, labels use
            ``palette.text_muted``, and the baseline uses
            ``palette.border``.

    Raises:
        ValueError: If any point's ``value_cents`` is negative.
    """
    if any(point.value_cents < 0 for point in points):
        raise ValueError("draw_line_chart does not support negative values")

    canvas.root_state.drawing_actions.clear()
    canvas.redraw()

    plot_height = max(height - LABEL_AREA_HEIGHT, 0.0)
    if points:
        max_value = max((point.value_cents for point in points), default=0) or 1
        slot_width = width / len(points)
        coordinates = [
            (
                index * slot_width + slot_width / 2,
                plot_height - (point.value_cents / max_value) * plot_height,
            )
            for index, point in enumerate(points)
        ]

        if len(coordinates) >= 2:
            with canvas.stroke(color=palette.accent, line_width=LINE_WIDTH):
                first_x, first_y = coordinates[0]
                canvas.move_to(first_x, first_y)
                for x, y in coordinates[1:]:
                    canvas.line_to(x, y)

        for (x, y), point in zip(coordinates, points, strict=True):
            with canvas.fill(color=palette.accent):
                canvas.rect(
                    x - POINT_MARKER_SIZE / 2,
                    y - POINT_MARKER_SIZE / 2,
                    POINT_MARKER_SIZE,
                    POINT_MARKER_SIZE,
                )
            _draw_centered_label(
                canvas,
                point.label,
                center_x=x,
                top_y=plot_height + LABEL_MARGIN,
                palette=palette,
            )

    _draw_baseline(canvas, width=width, y=plot_height, palette=palette)


def _draw_centered_label(
    canvas: toga.Canvas,
    text: str,
    *,
    center_x: float,
    top_y: float,
    palette: Palette,
) -> None:
    """Draw ``text`` horizontally centered on ``center_x``, top-aligned at ``top_y``.

    Args:
        canvas: The Canvas to draw onto.
        text: The label text.
        center_x: X coordinate the text should be horizontally centered on.
        top_y: Y coordinate of the top of the text.
        palette: Active color palette; the label uses ``palette.text_muted``.
    """
    text_width, _ = canvas.measure_text(text)
    with canvas.fill(color=palette.text_muted):
        canvas.fill_text(text, center_x - text_width / 2, top_y, baseline=Baseline.TOP)


def _draw_baseline(canvas: toga.Canvas, *, width: float, y: float, palette: Palette) -> None:
    """Draw a thin horizontal axis line across the full chart width.

    Args:
        canvas: The Canvas to draw onto.
        width: Width of the line, spanning the full plot area.
        y: Y coordinate of the line.
        palette: Active color palette; the line uses ``palette.border``.
    """
    with canvas.stroke(color=palette.border, line_width=1.0):
        canvas.move_to(0, y)
        canvas.line_to(width, y)
