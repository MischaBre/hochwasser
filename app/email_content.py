from __future__ import annotations

from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from app.config import Settings
from app.forecasting import Crossing, forecast_uncertainty_cm
from app.i18n import format_float, tr
from app.pegelonline import Measurement, StationInfo
from app.plotting import build_forecast_chart_html


def build_email(
    now: datetime,
    station: StationInfo,
    current: Measurement,
    historical_points: list[Measurement],
    forecast_points: list[Measurement],
    crossing: Crossing,
    settings: Settings,
    zone: ZoneInfo,
) -> tuple[str, str, str]:
    locale = settings.locale
    max_forecast = _get_max_forecast_point(forecast_points)

    max_forecast_line = f"{tr(locale, 'label_max_forecast_value')}: -"
    if max_forecast:
        max_ts_local = _format_datetime_local(max_forecast.timestamp, zone, locale)
        max_forecast_line = (
            f"{tr(locale, 'label_max_forecast_value')}: "
            f"{format_float(max_forecast.value, locale)} {station.unit} "
            f"({tr(locale, 'label_at')} {max_ts_local})"
        )

    subject = tr(
        locale,
        "subject",
        station=station.shortname,
        limit=format_float(settings.limit_cm, locale),
        unit=station.unit,
    )

    body = (
        f"{tr(locale, 'section_station_information')}\n"
        "-------------------\n"
        f"{tr(locale, 'label_station_uuid')}: {station.uuid}\n"
        f"{tr(locale, 'label_station_number')}: {station.number or '-'}\n"
        f"{tr(locale, 'label_short_name')}: {station.shortname}\n"
        f"{tr(locale, 'label_long_name')}: {station.longname}\n"
        f"{tr(locale, 'label_agency')}: {station.agency or '-'}\n"
        f"{tr(locale, 'label_water_body')}: {station.water_longname or station.water_shortname or '-'}\n"
        f"{tr(locale, 'label_water_shortname')}: {station.water_shortname or '-'}\n"
        f"{tr(locale, 'label_km')}: {format_float(station.km, locale) if station.km is not None else '-'}\n"
        f"{tr(locale, 'label_longitude')}: {format_float(station.longitude, locale, digits=4) if station.longitude is not None else '-'}\n"
        f"{tr(locale, 'label_latitude')}: {format_float(station.latitude, locale, digits=4) if station.latitude is not None else '-'}\n"
        f"{tr(locale, 'label_timeseries')}: {', '.join(ts.get('shortname', '?') for ts in station.timeseries if isinstance(ts, dict)) or '-'}\n\n"
        f"{tr(locale, 'section_alert_context')}\n"
        "-------------\n"
        f"{tr(locale, 'label_threshold')}: {format_float(settings.limit_cm, locale)} {station.unit}\n"
        f"{tr(locale, 'label_current_value')}: {format_float(current.value, locale)} {station.unit} "
        f"({tr(locale, 'label_at')} {_format_datetime_local(current.timestamp, zone, locale)})\n"
        f"{tr(locale, 'label_trigger_source')}: {_format_source(crossing.source, locale)}\n"
        f"{tr(locale, 'label_trigger_value')}: {format_float(crossing.value, locale)} {station.unit}\n"
        f"{tr(locale, 'label_trigger_time')}: {_format_datetime_local(crossing.timestamp, zone, locale)}\n\n"
        f"{max_forecast_line}\n\n"
        f"{tr(locale, 'section_forecast_data')}\n"
        "-----------------------\n"
        f"{_format_forecast_table(forecast_points, now, settings.limit_cm, station.unit, zone, locale)}\n"
    )

    html_body = _build_email_html(
        now,
        station,
        current,
        crossing,
        historical_points,
        forecast_points,
        settings,
        zone,
        max_forecast_line,
    )
    return subject, body, html_body


def _build_email_html(
    now: datetime,
    station: StationInfo,
    current: Measurement,
    crossing: Crossing,
    historical_points: list[Measurement],
    forecast_points: list[Measurement],
    settings: Settings,
    zone: ZoneInfo,
    max_forecast_line: str,
) -> str:
    locale = settings.locale
    station_timeseries = (
        ", ".join(
            ts.get("shortname", "?")
            for ts in station.timeseries
            if isinstance(ts, dict)
        )
        or "-"
    )

    table_html = _format_forecast_table_html(
        forecast_points,
        now,
        settings.limit_cm,
        station.unit,
        zone,
        locale,
    )
    chart_html = build_forecast_chart_html(
        historical_points,
        current,
        forecast_points,
        now,
        settings.limit_cm,
        station.unit,
        zone,
        locale,
    )

    return (
        "<html><body style='font-family:Arial,sans-serif;font-size:14px;color:#111'>"
        f"<h3>{escape(tr(locale, 'section_station_information'))}</h3>"
        f"<p>{escape(tr(locale, 'label_station_uuid'))}: {escape(station.uuid)}<br>"
        f"{escape(tr(locale, 'label_station_number'))}: {escape(station.number or '-')}<br>"
        f"{escape(tr(locale, 'label_short_name'))}: {escape(station.shortname)}<br>"
        f"{escape(tr(locale, 'label_long_name'))}: {escape(station.longname)}<br>"
        f"{escape(tr(locale, 'label_agency'))}: {escape(station.agency or '-')}<br>"
        f"{escape(tr(locale, 'label_water_body'))}: {escape(station.water_longname or station.water_shortname or '-')}<br>"
        f"{escape(tr(locale, 'label_water_shortname'))}: {escape(station.water_shortname or '-')}<br>"
        f"{escape(tr(locale, 'label_km'))}: {format_float(station.km, locale) if station.km is not None else '-'}<br>"
        f"{escape(tr(locale, 'label_longitude'))}: {format_float(station.longitude, locale, digits=4) if station.longitude is not None else '-'}<br>"
        f"{escape(tr(locale, 'label_latitude'))}: {format_float(station.latitude, locale, digits=4) if station.latitude is not None else '-'}<br>"
        f"{escape(tr(locale, 'label_timeseries'))}: {escape(station_timeseries)}</p>"
        f"<h3>{escape(tr(locale, 'section_alert_context'))}</h3>"
        f"<p>{escape(tr(locale, 'label_threshold'))}: {format_float(settings.limit_cm, locale)} {escape(station.unit)}<br>"
        f"{escape(tr(locale, 'label_current_value'))}: {format_float(current.value, locale)} {escape(station.unit)} "
        f"({escape(tr(locale, 'label_at'))} {_format_datetime_local(current.timestamp, zone, locale)})<br>"
        f"{escape(tr(locale, 'label_trigger_source'))}: {escape(_format_source(crossing.source, locale))}<br>"
        f"{escape(tr(locale, 'label_trigger_value'))}: {format_float(crossing.value, locale)} {escape(station.unit)}<br>"
        f"{escape(tr(locale, 'label_trigger_time'))}: {_format_datetime_local(crossing.timestamp, zone, locale)}<br>"
        f"{escape(max_forecast_line)}</p>"
        f"<h3>{escape(tr(locale, 'section_hydrograph'))}</h3>"
        f"{chart_html}"
        f"<h3>{escape(tr(locale, 'section_forecast_data'))}</h3>"
        f"{table_html}"
        "</body></html>"
    )


def _format_forecast_table(
    forecast_points: list[Measurement],
    reference_time: datetime,
    limit_cm: float,
    unit: str,
    zone: ZoneInfo,
    locale: str,
) -> str:
    if not forecast_points:
        return tr(locale, "message_no_forecast_points")

    header = (
        f"{tr(locale, 'table_timestamp'):<20} | {tr(locale, 'table_value'):>10} | "
        f"{tr(locale, 'table_above_limit'):<16} | {tr(locale, 'table_confidence'):<24}"
    )
    separator = "-" * len(header)
    rows = [header, separator]

    for point in forecast_points:
        local_ts = _format_datetime_local(point.timestamp, zone, locale)
        is_above = (
            tr(locale, "value_yes")
            if point.value >= limit_cm
            else tr(locale, "value_no")
        )
        conf = _format_confidence_band(
            point.value,
            unit,
            reference_time,
            point.timestamp,
            locale,
        )
        rows.append(
            f"{local_ts:<20} | {format_float(point.value, locale):>7} {unit:<2} | {is_above:<16} | {conf:<24}"
        )

    return "\n".join(rows)


def _format_forecast_table_html(
    forecast_points: list[Measurement],
    reference_time: datetime,
    limit_cm: float,
    unit: str,
    zone: ZoneInfo,
    locale: str,
) -> str:
    if not forecast_points:
        return f"<p>{escape(tr(locale, 'message_no_forecast_points'))}</p>"

    rows = []
    for point in forecast_points:
        local_ts = _format_datetime_local(point.timestamp, zone, locale)
        above = point.value >= limit_cm
        conf = _format_confidence_band(
            point.value,
            unit,
            reference_time,
            point.timestamp,
            locale,
        )
        value_html = f"{format_float(point.value, locale)} {escape(unit)}"
        if above:
            value_html = f"<strong style='color:#b00020'>{value_html}</strong>"
        rows.append(
            "<tr>"
            f"<td style='padding:6px;border:1px solid #ddd'>{local_ts}</td>"
            f"<td style='padding:6px;border:1px solid #ddd;text-align:right'>{value_html}</td>"
            f"<td style='padding:6px;border:1px solid #ddd'>{tr(locale, 'value_yes') if above else tr(locale, 'value_no')}</td>"
            f"<td style='padding:6px;border:1px solid #ddd'>{escape(conf)}</td>"
            "</tr>"
        )

    return (
        "<table style='border-collapse:collapse'>"
        "<thead><tr>"
        f"<th style='padding:6px;border:1px solid #ddd;text-align:left'>{escape(tr(locale, 'table_timestamp'))}</th>"
        f"<th style='padding:6px;border:1px solid #ddd;text-align:left'>{escape(tr(locale, 'table_value'))}</th>"
        f"<th style='padding:6px;border:1px solid #ddd;text-align:left'>{escape(tr(locale, 'table_above_limit'))}</th>"
        f"<th style='padding:6px;border:1px solid #ddd;text-align:left'>{escape(tr(locale, 'table_confidence'))}</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )


def _format_confidence_band(
    value: float,
    unit: str,
    reference_time: datetime,
    timestamp: datetime,
    locale: str,
) -> str:
    uncertainty = forecast_uncertainty_cm(reference_time, timestamp)
    if uncertainty is None:
        return "-"
    min_value = value - uncertainty
    max_value = value + uncertainty
    return (
        f"{format_float(min_value, locale)}..{format_float(max_value, locale)} {unit}"
    )


def _get_max_forecast_point(forecast_points: list[Measurement]) -> Measurement | None:
    if not forecast_points:
        return None
    return max(forecast_points, key=lambda p: p.value)


def _format_datetime_local(timestamp: datetime, zone: ZoneInfo, locale: str) -> str:
    local_ts = timestamp.astimezone(zone)
    if locale == "de":
        return local_ts.strftime("%d.%m.%Y %H:%M %Z")
    return local_ts.strftime("%Y-%m-%d %H:%M %Z")


def _format_source(source: str, locale: str) -> str:
    if source == "current":
        return tr(locale, "trigger_source_current")
    if source == "official":
        return tr(locale, "trigger_source_official")
    return source
