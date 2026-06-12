# mcr/args.py
"""Argument normalization and API parameter mapping helpers."""

from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

API_PARAM_MAP: dict[str, dict[str, str]] = {
    'campaigns': {
        'limit': 'count',
        'audience_id': 'list_id',
        'start_date': 'since_send_time',
        'end_date': 'before_send_time',
    },
    'audiences': {
        'limit': 'count',
        'start_date': 'since_campaign_last_sent',
        'end_date': 'before_campaign_last_sent',
    },
    'contacts': {
        'limit': 'count',
        'start_date': 'since_timestamp_opt',
        'end_date': 'before_timestamp_opt',
    },
}

def _parse_iso_date(value: str, field_name: str) -> date:
    """
    Parse an ISO date string into a date object.

    Args:
        value (str): Date string in YYYY-MM-DD format.
        field_name (str): Field name for validation errors.

    Returns:
        date: Parsed date object.
    """
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f'Invalid {field_name} value {value!r}. Expected YYYY-MM-DD.'
        ) from exc


def _resolve_date_range(normalized_args: dict[str, Any]) -> tuple[str | None, str | None]:
    """
    Resolve explicit or relative date arguments into a normalized range.

    Args:
        normalized_args (dict[str, Any]): Normalized argument state.

    Returns:
        tuple[str | None, str | None]: Resolved (start_date, end_date).
    """
    start_date = normalized_args.get('start_date')
    end_date = normalized_args.get('end_date')
    last = normalized_args.get('last')
    previous = normalized_args.get('previous')

    has_explicit_range = bool(start_date or end_date)
    has_last = last is not None
    has_previous = previous is not None

    if has_last and has_previous:
        raise ValueError('--last and --previous are mutually exclusive.')
    if has_explicit_range and (has_last or has_previous):
        raise ValueError(
            'Do not combine --start-date/--end-date with --last or --previous.'
        )

    if has_previous:
        return _resolve_previous_period(previous)

    if has_last:
        if last <= 0:
            raise ValueError('--last must be a positive integer.')

        today = date.today()
        range_end = today
        range_start = today - timedelta(days=last - 1)

        return _to_day_boundary_datetimes(range_start, range_end)

    parsed_start = _parse_iso_date(start_date, 'start_date') if start_date else None
    parsed_end = _parse_iso_date(end_date, 'end_date') if end_date else None

    if parsed_start and parsed_end and parsed_start > parsed_end:
        raise ValueError('--start-date must be earlier than or equal to --end-date.')

    if not parsed_start and not parsed_end:
        return None, None

    return _to_day_boundary_datetimes(parsed_start, parsed_end)


def _resolve_previous_period(period: str) -> tuple[str, str]:
    """
    Resolve named period into prior completed period boundaries.

    Args:
        period (str): One of week, month, quarter, or year.

    Returns:
        tuple[str, str]: Prior completed period start and end datetimes.
    """
    today = date.today()

    if period == 'week':
        current_week_start = today - timedelta(days=today.weekday())
        period_end = current_week_start - timedelta(days=1)
        period_start = period_end - timedelta(days=6)
        return _to_day_boundary_datetimes(period_start, period_end)

    if period == 'month':
        current_month_start = today.replace(day=1)
        period_end = current_month_start - timedelta(days=1)
        period_start = period_end.replace(day=1)
        return _to_day_boundary_datetimes(period_start, period_end)

    if period == 'quarter':
        current_quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        current_quarter_start = date(today.year, current_quarter_start_month, 1)
        period_end = current_quarter_start - timedelta(days=1)
        previous_quarter_start_month = ((period_end.month - 1) // 3) * 3 + 1
        period_start = date(period_end.year, previous_quarter_start_month, 1)
        return _to_day_boundary_datetimes(period_start, period_end)

    if period == 'year':
        previous_year = today.year - 1
        period_start = date(previous_year, 1, 1)
        period_end = date(previous_year, 12, 31)
        return _to_day_boundary_datetimes(period_start, period_end)

    raise ValueError(
        "Invalid --previous value. Expected one of 'week', 'month', 'quarter', 'year'."
    )


def _to_day_boundary_datetimes(
    start_date: date | None,
    end_date: date | None,
) -> tuple[str | None, str | None]:
    """
    Convert date values to UTC day-boundary datetime strings.

    Args:
        start_date (date | None): Start date value.
        end_date (date | None): End date value.

    Returns:
        tuple[str | None, str | None]: Datetime range as ISO 8601 strings.
    """
    start_value: str | None = None
    end_value: str | None = None

    if start_date is not None:
        start_value = datetime.combine(
            start_date,
            time(0, 0, 0),
            tzinfo=timezone.utc,
        ).isoformat()

    if end_date is not None:
        end_value = datetime.combine(
            end_date,
            time(23, 59, 59),
            tzinfo=timezone.utc,
        ).isoformat()

    return start_value, end_value


def build_api_params(normalized_args: dict[str, Any]) -> dict[str, Any]:
    """
    Build query parameters for supported Mailchimp endpoints.

    Args:
        normalized_args (dict[str, Any]): Normalized arguments dictionary.

    Returns:
        dict[str, Any]: Query parameter dictionary for the active scope.
    """
    report = normalized_args.get('report')
    if not report or report not in API_PARAM_MAP:
        return {}

    param_map = API_PARAM_MAP[report]
    api_params: dict[str, Any] = {}

    if normalized_args.get('limit') is not None and 'limit' in param_map:
        api_params[param_map['limit']] = normalized_args['limit']

    if report == 'campaigns' and normalized_args.get('audience_id') is not None:
        audience_key = param_map.get('audience_id')
        if audience_key:
            api_params[audience_key] = normalized_args['audience_id']

    if normalized_args.get('start_date') is not None and 'start_date' in param_map:
        api_params[param_map['start_date']] = normalized_args['start_date']
    if normalized_args.get('end_date') is not None and 'end_date' in param_map:
        api_params[param_map['end_date']] = normalized_args['end_date']

    return {key: value for key, value in api_params.items() if value is not None}


def normalize_args(args: argparse.Namespace) -> dict[str, Any]:
    """
    Normalize parsed argparse values into a stable execution structure.

    Args:
        args (argparse.Namespace): Parsed CLI arguments.

    Returns:
        dict[str, Any]: Normalized arguments with API params and local filters.
    """
    normalized: dict[str, Any] = {
        'report': getattr(args, 'report', None),
        'config': getattr(args, 'config', None),
        'output': getattr(args, 'output', None),
        'savefile': getattr(args, 'savefile', None),
        'limit': getattr(args, 'limit', None),
        'audience_id': getattr(args, 'audience_id', None),
        'audience': getattr(args, 'audience', None),
        'start_date': getattr(args, 'start_date', None),
        'end_date': getattr(args, 'end_date', None),
        'last': getattr(args, 'last', None),
        'previous': getattr(args, 'previous', None),
        'subject': getattr(args, 'subject', None),
        'email': getattr(args, 'email', None),
        'name': getattr(args, 'name', None),
        'api_params': {},
        'filters': {},
    }

    resolved_start, resolved_end = _resolve_date_range(normalized)
    normalized['start_date'] = resolved_start
    normalized['end_date'] = resolved_end

    normalized['filters'] = {
        'subject': normalized.get('subject'),
        'email': normalized.get('email'),
        'name': normalized.get('name'),
    }
    normalized['api_params'] = build_api_params(normalized)
    return normalized