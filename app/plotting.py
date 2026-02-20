from __future__ import annotations

import math
from base64 import b64encode
from datetime import datetime, timedelta
from html import escape
from io import BytesIO
from zoneinfo import ZoneInfo

import matplotlib
import matplotlib.dates as mdates
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator

from app.forecasting import forecast_uncertainty_cm
from app.i18n import format_float, tr
from app.pegelonline import Measurement

matplotlib.use("Agg")


def build_forecast_chart_html(
    historical_points: list[Measurement],
    current: Measurement,
    forecast_points: list[Measurement],
    reference_time: datetime,
    limit_cm: float,
    unit: str,
    zone: ZoneInfo,
    locale: str,
) -> str:
    series = sorted(
        [*historical_points, current, *forecast_points],
        key=lambda point: point.timestamp,
    )
    if len(series) < 2:
        return f"<p>{escape(tr(locale, 'message_not_enough_chart_points'))}</p>"

    start_ts = series[0].timestamp
    end_ts = series[-1].timestamp
    if end_ts <= start_ts:
        return f"<p>{escape(tr(locale, 'message_not_enough_chart_points'))}</p>"

    values = [point.value for point in series]
    values.append(limit_cm)
    lower_band: list[float] = []
    upper_band: list[float] = []
    for point in forecast_points:
        uncertainty = forecast_uncertainty_cm(reference_time, point.timestamp)
        if uncertainty is None:
            continue
        lower_band.append(point.value - uncertainty)
        upper_band.append(point.value + uncertainty)
        values.append(point.value - uncertainty)
        values.append(point.value + uncertainty)

    min_value = min(values)
    max_value = max(values)
    if max_value - min_value < 1.0:
        min_value -= 1.0
        max_value += 1.0
    else:
        padding = (max_value - min_value) * 0.08
        min_value -= padding
        max_value += padding

    fig, ax = plt.subplots(figsize=(10.5, 4.2), dpi=110)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    for y_value in range(
        int(math.floor(min_value / 10.0) * 10),
        int(math.ceil(max_value / 10.0) * 10) + 1,
        10,
    ):
        ax.axhline(y=float(y_value), color="#e9e9e9", linewidth=0.9, zorder=0)

    start_local = start_ts.astimezone(zone)
    end_local = end_ts.astimezone(zone)
    first_tick_local = start_local.replace(minute=0, second=0, microsecond=0)
    remainder = first_tick_local.hour % 12
    if remainder:
        first_tick_local += timedelta(hours=12 - remainder)
    if first_tick_local < start_local:
        first_tick_local += timedelta(hours=12)

    tick_positions: list[datetime] = []
    tick_time_local = first_tick_local
    while tick_time_local <= end_local:
        tick_time = tick_time_local.astimezone(start_ts.tzinfo)
        tick_positions.append(tick_time)
        if tick_time_local.hour == 0:
            ax.axvline(tick_time, color="#c6c6c6", linewidth=1.1, zorder=0)
        else:
            ax.axvline(tick_time, color="#e6e6e6", linewidth=0.9, zorder=0)
        tick_time_local += timedelta(hours=12)

    ax.axhline(limit_cm, color="#b00020", linewidth=1.6, zorder=2)

    for idx in range(len(series) - 1):
        first = series[idx]
        second = series[idx + 1]
        above_first = first.value >= limit_cm
        above_second = second.value >= limit_cm

        if above_first == above_second:
            ax.plot(
                [first.timestamp, second.timestamp],
                [first.value, second.value],
                color="#b00020" if above_first else "#1f4e79",
                linewidth=1.6,
                zorder=3,
            )
            continue

        if second.value == first.value:
            ax.plot(
                [first.timestamp, second.timestamp],
                [first.value, second.value],
                color="#b00020",
                linewidth=1.6,
                zorder=3,
            )
            continue

        ratio = (limit_cm - first.value) / (second.value - first.value)
        ratio = max(0.0, min(1.0, ratio))
        crossing_time = first.timestamp + timedelta(
            seconds=(second.timestamp - first.timestamp).total_seconds() * ratio
        )

        ax.plot(
            [first.timestamp, crossing_time],
            [first.value, limit_cm],
            color="#b00020" if above_first else "#1f4e79",
            linewidth=1.6,
            zorder=3,
        )
        ax.plot(
            [crossing_time, second.timestamp],
            [limit_cm, second.value],
            color="#b00020" if above_second else "#1f4e79",
            linewidth=1.6,
            zorder=3,
        )

    if lower_band:
        forecast_with_uncertainty = [
            point
            for point in forecast_points
            if forecast_uncertainty_cm(reference_time, point.timestamp) is not None
        ]
        forecast_ts = [point.timestamp for point in forecast_with_uncertainty]
        ax.fill_between(
            forecast_ts,
            lower_band,
            upper_band,
            color="#d9d9d9",
            alpha=0.12,
            zorder=1,
        )
        ax.plot(
            forecast_ts,
            lower_band,
            color="#b8b8b8",
            linewidth=1.0,
            linestyle=(0, (3, 4)),
            zorder=2,
        )
        ax.plot(
            forecast_ts,
            upper_band,
            color="#b8b8b8",
            linewidth=1.0,
            linestyle=(0, (3, 4)),
            zorder=2,
        )

    if start_ts <= reference_time <= end_ts:
        ax.axvline(
            reference_time,
            color="#1976d2",
            linewidth=1.4,
            linestyle=(0, (3, 3)),
            zorder=2,
        )
        ax.text(
            reference_time,
            max_value,
            tr(locale, "chart_now"),
            color="#1976d2",
            fontsize=9,
            va="bottom",
            ha="left",
        )

    def y_formatter(value: float, _pos: float) -> str:
        return format_float(value, locale)

    def x_formatter(x_value: float, _pos: float) -> str:
        tick_dt = mdates.num2date(x_value)
        return _format_x_tick_label(tick_dt, zone, locale)

    ax.yaxis.set_major_locator(MultipleLocator(10))
    ax.yaxis.set_major_formatter(FuncFormatter(y_formatter))
    if tick_positions:
        ax.set_xticks(tick_positions)
    ax.xaxis.set_major_formatter(FuncFormatter(x_formatter))

    ax.set_xlim(start_ts, end_ts)
    ax.set_ylim(min_value, max_value)
    ax.tick_params(axis="x", labelsize=9)
    ax.tick_params(axis="y", labelsize=9)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#bcbcbc")
    ax.spines["bottom"].set_color("#bcbcbc")

    ax.text(
        0.01,
        0.98,
        tr(locale, "chart_threshold", limit=format_float(limit_cm, locale), unit=unit),
        transform=ax.transAxes,
        color="#b00020",
        fontsize=9,
        va="top",
        ha="left",
    )
    ax.set_xlabel(
        tr(locale, "chart_time_label", timezone=zone.key),
        fontsize=9,
        color="#555",
    )

    fig.tight_layout()
    png_buffer = BytesIO()
    fig.savefig(png_buffer, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)

    encoded = b64encode(png_buffer.getvalue()).decode("ascii")
    return (
        "<div>"
        f"<img alt='{escape(tr(locale, 'section_hydrograph'))}' "
        "style='max-width:100%;height:auto;border:1px solid #ddd' "
        f"src='data:image/png;base64,{encoded}'/>"
        "<p style='margin:6px 0 0;color:#555;font-size:12px'>"
        f"{escape(tr(locale, 'chart_legend'))}"
        "</p>"
        "</div>"
    )


def _format_x_tick_label(timestamp: datetime, zone: ZoneInfo, locale: str) -> str:
    local_ts = timestamp.astimezone(zone)
    if locale == "de":
        return local_ts.strftime("%d.%m %H:%M")
    return local_ts.strftime("%m/%d %H:%M")
