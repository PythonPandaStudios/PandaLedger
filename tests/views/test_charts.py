"""Unit tests for the hand-rolled Canvas bar/line chart engine (PRD §7.1, §3)."""

from __future__ import annotations

import pytest
import toga
from toga.widgets.canvas import Fill, FillText, LineTo, MoveTo, Rect, Stroke

from pandaledger.views.charts import (
    LABEL_AREA_HEIGHT,
    LABEL_MARGIN,
    POINT_MARKER_SIZE,
    BarDatum,
    LinePoint,
    draw_bar_chart,
    draw_line_chart,
)
from pandaledger.views.theme import LIGHT_PALETTE


def _fills(canvas: toga.Canvas) -> list[Fill]:
    return [a for a in canvas.root_state.drawing_actions if isinstance(a, Fill)]


def _strokes(canvas: toga.Canvas) -> list[Stroke]:
    return [a for a in canvas.root_state.drawing_actions if isinstance(a, Stroke)]


class TestDrawBarChart:
    def test_empty_data_draws_only_the_baseline(self) -> None:
        """No bars, no labels — just the axis stroke."""
        canvas = toga.Canvas()

        draw_bar_chart(canvas, [], width=200, height=100, palette=LIGHT_PALETTE)

        assert _fills(canvas) == []
        strokes = _strokes(canvas)
        assert len(strokes) == 1
        [move_to, line_to] = strokes[0].drawing_actions
        assert isinstance(move_to, MoveTo)
        assert isinstance(line_to, LineTo)
        assert move_to.x == 0
        assert line_to.x == 200

    def test_negative_value_is_rejected(self) -> None:
        """A negative bar value raises rather than drawing something wrong."""
        canvas = toga.Canvas()

        with pytest.raises(ValueError, match="negative"):
            draw_bar_chart(
                canvas,
                [BarDatum("Rent", -100)],
                width=200,
                height=100,
                palette=LIGHT_PALETTE,
            )

    def test_single_full_height_bar_spans_the_plot_area(self) -> None:
        """A lone bar that's also the max value fills the full plot height."""
        canvas = toga.Canvas()
        plot_height = 100 - LABEL_AREA_HEIGHT

        draw_bar_chart(
            canvas,
            [BarDatum("Rent", 50_000)],
            width=200,
            height=100,
            palette=LIGHT_PALETTE,
        )

        fills = _fills(canvas)
        # One fill for the bar rect, one for its label.
        assert len(fills) == 2
        [rect] = fills[0].drawing_actions
        assert isinstance(rect, Rect)
        assert rect.width == pytest.approx(200 * 0.7)
        assert rect.height == pytest.approx(plot_height)
        assert rect.y == pytest.approx(0)

    def test_bar_height_scales_relative_to_the_max_value(self) -> None:
        """A bar at half the max value is half the plot height tall."""
        canvas = toga.Canvas()
        plot_height = 100 - LABEL_AREA_HEIGHT

        draw_bar_chart(
            canvas,
            [BarDatum("Groceries", 25_000), BarDatum("Rent", 50_000)],
            width=200,
            height=100,
            palette=LIGHT_PALETTE,
        )

        fills = _fills(canvas)
        groceries_rect = fills[0].drawing_actions[0]
        rent_rect = fills[2].drawing_actions[0]
        assert isinstance(groceries_rect, Rect)
        assert isinstance(rent_rect, Rect)
        assert groceries_rect.height == pytest.approx(plot_height / 2)
        assert rent_rect.height == pytest.approx(plot_height)

    def test_all_zero_values_draw_zero_height_bars_without_dividing_by_zero(self) -> None:
        """Every bar at zero shouldn't raise — they just have no height."""
        canvas = toga.Canvas()

        draw_bar_chart(
            canvas,
            [BarDatum("Empty", 0)],
            width=200,
            height=100,
            palette=LIGHT_PALETTE,
        )

        [bar_fill, _label_fill] = _fills(canvas)
        rect = bar_fill.drawing_actions[0]
        assert isinstance(rect, Rect)
        assert rect.height == 0

    def test_label_is_horizontally_centered_under_its_bar(self) -> None:
        """The label's left edge accounts for its measured text width."""
        canvas = toga.Canvas()

        draw_bar_chart(
            canvas,
            [BarDatum("AB", 10_000)],
            width=200,
            height=100,
            palette=LIGHT_PALETTE,
        )

        [_bar_fill, label_fill] = _fills(canvas)
        [fill_text] = label_fill.drawing_actions
        assert isinstance(fill_text, FillText)
        # Dummy backend's system-font metric: width = len(text) * 12.
        text_width, _ = canvas.measure_text("AB")
        expected_x = 100 - text_width / 2  # slot center for a single bar over width=200
        assert fill_text.x == pytest.approx(expected_x)
        assert fill_text.y == pytest.approx((100 - LABEL_AREA_HEIGHT) + LABEL_MARGIN)

    def test_redrawing_clears_previous_content(self) -> None:
        """A second call doesn't leave the first call's shapes behind."""
        canvas = toga.Canvas()
        draw_bar_chart(
            canvas,
            [BarDatum("A", 100), BarDatum("B", 200)],
            width=200,
            height=100,
            palette=LIGHT_PALETTE,
        )
        first_fill_count = len(_fills(canvas))

        draw_bar_chart(
            canvas,
            [BarDatum("A", 100)],
            width=200,
            height=100,
            palette=LIGHT_PALETTE,
        )

        assert len(_fills(canvas)) < first_fill_count


class TestDrawLineChart:
    def test_empty_points_draws_only_the_baseline(self) -> None:
        canvas = toga.Canvas()

        draw_line_chart(canvas, [], width=200, height=100, palette=LIGHT_PALETTE)

        assert _fills(canvas) == []
        assert len(_strokes(canvas)) == 1

    def test_negative_value_is_rejected(self) -> None:
        canvas = toga.Canvas()

        with pytest.raises(ValueError, match="negative"):
            draw_line_chart(
                canvas,
                [LinePoint("Jan", -1)],
                width=200,
                height=100,
                palette=LIGHT_PALETTE,
            )

    def test_single_point_draws_a_marker_but_no_connecting_line(self) -> None:
        """One point has no slope to draw — only its marker and label, plus baseline."""
        canvas = toga.Canvas()

        draw_line_chart(
            canvas,
            [LinePoint("Jan", 10_000)],
            width=200,
            height=100,
            palette=LIGHT_PALETTE,
        )

        # Baseline is the only stroke; no line-connecting stroke was added.
        assert len(_strokes(canvas)) == 1
        fills = _fills(canvas)
        assert len(fills) == 2  # marker rect + label
        [marker] = fills[0].drawing_actions
        assert isinstance(marker, Rect)
        assert marker.width == pytest.approx(POINT_MARKER_SIZE)

    def test_two_points_draw_a_connecting_line_between_them(self) -> None:
        canvas = toga.Canvas()
        plot_height = 100 - LABEL_AREA_HEIGHT

        draw_line_chart(
            canvas,
            [LinePoint("Jan", 0), LinePoint("Feb", 20_000)],
            width=200,
            height=100,
            palette=LIGHT_PALETTE,
        )

        strokes = _strokes(canvas)
        # The connecting-line stroke is drawn before the baseline stroke.
        assert len(strokes) == 2
        line_stroke = strokes[0]
        [move_to, line_to] = line_stroke.drawing_actions
        assert isinstance(move_to, MoveTo)
        assert isinstance(line_to, LineTo)
        # Jan (value 0) sits on the plot floor; Feb (the max) sits at the top.
        assert move_to.y == pytest.approx(plot_height)
        assert line_to.y == pytest.approx(0)

    def test_redrawing_clears_previous_content(self) -> None:
        canvas = toga.Canvas()
        draw_line_chart(
            canvas,
            [LinePoint("Jan", 100), LinePoint("Feb", 200)],
            width=200,
            height=100,
            palette=LIGHT_PALETTE,
        )
        first_stroke_count = len(_strokes(canvas))

        draw_line_chart(
            canvas,
            [LinePoint("Jan", 100)],
            width=200,
            height=100,
            palette=LIGHT_PALETTE,
        )

        assert len(_strokes(canvas)) < first_stroke_count
