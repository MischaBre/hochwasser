from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import AlertJob
from app.email_templates import render_email_template
from app.forecasting import Crossing, forecast_uncertainty_cm
from app.locale_utils import format_float
from app.pegelonline import Measurement, StationInfo
from app.plotting import build_forecast_chart_payload
from app.translator import translate


def build_email(
    now: datetime,
    station: StationInfo,
    current: Measurement,
    historical_points: list[Measurement],
    forecast_points: list[Measurement],
    crossing: Crossing,
    limit_cm: float,
    locale: str,
    zone: ZoneInfo,
) -> tuple[str, str, str]:
    max_forecast = _get_max_forecast_point(forecast_points)

    context = _build_alert_email_context(
        now=now,
        station=station,
        current=current,
        historical_points=historical_points,
        forecast_points=forecast_points,
        crossing=crossing,
        limit_cm=limit_cm,
        locale=locale,
        zone=zone,
        max_forecast=max_forecast,
    )
    subject = render_email_template(locale, "email/alert_subject.txt.j2", **context)
    body = render_email_template(locale, "email/alert_body.txt.j2", **context)
    html_body = render_email_template(locale, "email/alert_body.html.j2", **context)
    return subject, body, html_body


def _build_alert_email_context(
    now: datetime,
    station: StationInfo,
    current: Measurement,
    historical_points: list[Measurement],
    forecast_points: list[Measurement],
    crossing: Crossing,
    limit_cm: float,
    locale: str,
    zone: ZoneInfo,
    max_forecast: Measurement | None,
) -> dict[str, object]:
    station_timeseries = (
        ", ".join(
            ts.get("shortname", "?")
            for ts in station.timeseries
            if isinstance(ts, dict)
        )
        or "-"
    )

    forecast_rows = _build_forecast_rows(
        forecast_points,
        now,
        limit_cm,
        station.unit,
        zone,
        locale,
    )
    chart_payload = build_forecast_chart_payload(
        historical_points,
        current,
        forecast_points,
        now,
        limit_cm,
        station.unit,
        zone,
        locale,
    )

    return {
        "station_uuid": station.uuid,
        "station_number": station.number or "-",
        "station_shortname": station.shortname,
        "station_longname": station.longname,
        "station_agency": station.agency or "-",
        "station_water_body": station.water_longname or station.water_shortname or "-",
        "station_water_shortname": station.water_shortname or "-",
        "station_km": format_float(station.km, locale)
        if station.km is not None
        else "-",
        "station_longitude": (
            format_float(station.longitude, locale, digits=4)
            if station.longitude is not None
            else "-"
        ),
        "station_latitude": (
            format_float(station.latitude, locale, digits=4)
            if station.latitude is not None
            else "-"
        ),
        "station_timeseries": station_timeseries,
        "station_unit": station.unit,
        "limit_formatted": format_float(limit_cm, locale),
        "current_value_formatted": format_float(current.value, locale),
        "current_timestamp_local": _format_datetime_local(
            current.timestamp, zone, locale
        ),
        "trigger_source": _format_source(crossing.source, locale),
        "trigger_value_formatted": format_float(crossing.value, locale),
        "trigger_time_local": _format_datetime_local(crossing.timestamp, zone, locale),
        "max_forecast_value_with_unit": (
            f"{format_float(max_forecast.value, locale)} {station.unit}"
            if max_forecast is not None
            else None
        ),
        "max_forecast_time_local": (
            _format_datetime_local(max_forecast.timestamp, zone, locale)
            if max_forecast is not None
            else None
        ),
        "forecast_rows": forecast_rows,
        "message_no_forecast_points": translate(locale, "message_no_forecast_points"),
        "table_timestamp_label": translate(locale, "table_timestamp"),
        "table_value_label": translate(locale, "table_value"),
        "table_above_limit_label": translate(locale, "table_above_limit"),
        "table_confidence_label": translate(locale, "table_confidence"),
        "chart_image_data_uri": chart_payload["image_data_uri"],
        "chart_alt": chart_payload["alt"],
        "chart_legend": chart_payload["legend"],
        "chart_message": chart_payload["message"],
    }


def _build_forecast_rows(
    forecast_points: list[Measurement],
    reference_time: datetime,
    limit_cm: float,
    unit: str,
    zone: ZoneInfo,
    locale: str,
) -> list[dict[str, str | bool]]:
    rows: list[dict[str, str | bool]] = []

    for point in forecast_points:
        local_ts = _format_datetime_local(point.timestamp, zone, locale)
        is_above_limit = point.value >= limit_cm
        is_above_label = (
            translate(locale, "value_yes")
            if is_above_limit
            else translate(locale, "value_no")
        )
        conf = _format_confidence_band(
            point.value,
            unit,
            reference_time,
            point.timestamp,
            locale,
        )
        value_with_unit = f"{format_float(point.value, locale)} {unit}"
        rows.append(
            {
                "timestamp_local": local_ts,
                "value_with_unit": value_with_unit,
                "above_limit": is_above_limit,
                "above_limit_label": is_above_label,
                "confidence": conf,
            }
        )

    return rows


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
        return translate(locale, "trigger_source_current")
    if source == "official":
        return translate(locale, "trigger_source_official")
    return source


def build_notification_payload(
    now: datetime,
    station: StationInfo,
    current: Measurement,
    historical_points: list[Measurement],
    future_forecast: list[Measurement],
    job: AlertJob,
    state: str,
    crossing: Crossing | None,
    predicted_crossing_at: datetime | None,
    predicted_end_at: datetime | None,
    zone: ZoneInfo,
) -> tuple[str, str, str | None]:
    state_label = translate(job.locale, f"state_{state}")
    subject = render_email_template(
        job.locale,
        "email/state_update_subject.txt.j2",
        station_shortname=station.shortname,
        state_label=state_label,
    )

    if crossing is not None:
        _, body, html_body = build_email(
            now,
            station,
            current,
            historical_points,
            future_forecast,
            crossing,
            job.limit_cm,
            job.locale,
            zone,
        )
        state_prefix = render_email_template(
            job.locale,
            "email/state_update_prefix.txt.j2",
            state_label=state_label,
        )
        body = f"{state_prefix}\n{body}"
        return subject, body, html_body

    crossing_time = (
        predicted_crossing_at.astimezone(zone).isoformat()
        if predicted_crossing_at is not None
        else translate(job.locale, "message_not_available")
    )
    end_time = (
        predicted_end_at.astimezone(zone).isoformat()
        if predicted_end_at is not None
        else translate(job.locale, "message_not_available")
    )
    body = render_email_template(
        job.locale,
        "email/state_update_body.txt.j2",
        state_label=state_label,
        station_uuid=station.uuid,
        current_value_formatted=format_float(current.value, job.locale),
        station_unit=station.unit,
        limit_formatted=format_float(job.limit_cm, job.locale),
        crossing_time=crossing_time,
        end_time=end_time,
    )
    return subject, body, None
