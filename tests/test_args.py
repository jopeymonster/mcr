"""Tests for argument normalization and API parameter mapping."""

from __future__ import annotations

import argparse
from datetime import date, timedelta

import pytest

from mcr.args import normalize_args


def namespace(**values: object) -> argparse.Namespace:
    """Build an argparse namespace with default CLI fields."""
    defaults = {
        'report': 'campaigns',
        'config': 'config/auth.json',
        'output': 'json',
        'savefile': None,
        'limit': 25,
        'audience_id': None,
        'audience': None,
        'start_date': None,
        'end_date': None,
        'last': None,
        'previous': None,
        'subject': None,
        'email': None,
        'name': None,
    }
    defaults.update(values)
    return argparse.Namespace(**defaults)


def test_explicit_start_and_end_dates_normalize_to_api_params() -> None:
    """Explicit dates should normalize to report-specific API params."""
    normalized = normalize_args(
        namespace(start_date='2026-01-02', end_date='2026-01-05')
    )

    assert normalized['start_date'] == '2026-01-02T00:00:00+00:00'
    assert normalized['end_date'] == '2026-01-05T23:59:59+00:00'
    assert normalized['api_params']['since_send_time'] == normalized['start_date']
    assert normalized['api_params']['before_send_time'] == normalized['end_date']


def test_last_normalizes_to_recent_date_range() -> None:
    """Last should use an inclusive range ending today."""
    normalized = normalize_args(namespace(last=3))
    today = date.today()
    start = today - timedelta(days=2)

    assert normalized['start_date'] == f'{start.isoformat()}T00:00:00+00:00'
    assert normalized['end_date'] == f'{today.isoformat()}T23:59:59+00:00'


def test_previous_month_normalizes_to_completed_month() -> None:
    """Previous month should resolve to the prior completed calendar month."""
    normalized = normalize_args(namespace(previous='month'))
    today = date.today()
    current_month_start = today.replace(day=1)
    previous_month_end = current_month_start - timedelta(days=1)
    previous_month_start = previous_month_end.replace(day=1)

    assert normalized['start_date'] == (
        f'{previous_month_start.isoformat()}T00:00:00+00:00'
    )
    assert normalized['end_date'] == f'{previous_month_end.isoformat()}T23:59:59+00:00'


def test_explicit_dates_cannot_be_combined_with_last() -> None:
    """Explicit and relative date options should be mutually exclusive."""
    with pytest.raises(ValueError, match='Do not combine'):
        normalize_args(namespace(start_date='2026-01-01', last=7))


def test_last_and_previous_cannot_be_combined() -> None:
    """Last and previous should be mutually exclusive."""
    with pytest.raises(ValueError, match='mutually exclusive'):
        normalize_args(namespace(last=7, previous='week'))


def test_api_param_mapping_for_campaign_audience_limit_and_dates() -> None:
    """Campaign CLI args should map to Mailchimp API params."""
    normalized = normalize_args(
        namespace(
            audience_id='aud123',
            limit=50,
            start_date='2026-02-01',
            end_date='2026-02-28',
        )
    )

    assert normalized['api_params'] == {
        'count': 50,
        'list_id': 'aud123',
        'since_send_time': '2026-02-01T00:00:00+00:00',
        'before_send_time': '2026-02-28T23:59:59+00:00',
    }


def test_api_param_mapping_for_contacts_dates_and_limit() -> None:
    """Contacts CLI args should map date and limit params."""
    normalized = normalize_args(
        namespace(
            report='contacts',
            audience_id='aud123',
            start_date='2026-03-01',
            end_date='2026-03-31',
        )
    )

    assert normalized['api_params'] == {
        'count': 25,
        'since_timestamp_opt': '2026-03-01T00:00:00+00:00',
        'before_timestamp_opt': '2026-03-31T23:59:59+00:00',
    }


def test_normalize_args_preserves_local_filters_outside_api_params() -> None:
    """Local filters should stay separate from API parameter mapping."""
    normalized = normalize_args(
        namespace(report='campaigns', subject='launch', email='ada', name='Ada')
    )

    assert normalized['filters'] == {
        'subject': 'launch',
        'email': 'ada',
        'name': 'Ada',
    }
    assert 'subject' not in normalized['api_params']
    assert 'email' not in normalized['api_params']
    assert 'name' not in normalized['api_params']
