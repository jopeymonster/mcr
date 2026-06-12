"""Tests for local post-fetch filters."""

from __future__ import annotations

from mcr.filters import apply_local_filters


def test_campaign_subject_filter_is_case_insensitive_partial_match() -> None:
    """Campaign subject filters should match subject text locally."""
    rows = [
        {'id': 'a', 'subject_line': 'Spring Launch'},
        {'id': 'b', 'subject_line': 'Winter Update'},
    ]

    assert apply_local_filters('campaigns', rows, {'subject': 'spring'}) == [rows[0]]


def test_contacts_email_filter_is_case_insensitive_partial_match() -> None:
    """Contact email filters should match email address locally."""
    rows = [
        {'id': 'a', 'email_address': 'Alpha@Example.com'},
        {'id': 'b', 'email_address': 'beta@example.com'},
    ]

    assert apply_local_filters('contacts', rows, {'email': 'alpha@'}) == [rows[0]]


def test_contacts_name_filter_matches_normalized_name_fields() -> None:
    """Contact name filters should match available normalized names."""
    rows = [
        {'id': 'a', 'full_name': '', 'first_name': 'Ada', 'last_name': 'Lovelace'},
        {'id': 'b', 'full_name': 'Grace Hopper', 'first_name': '', 'last_name': ''},
    ]

    assert apply_local_filters('contacts', rows, {'name': 'hopper'}) == [rows[1]]
    assert apply_local_filters('contacts', rows, {'name': 'ada'}) == [rows[0]]


def test_local_filter_empty_match_returns_empty_result() -> None:
    """Local filters should cleanly return an empty list when no rows match."""
    rows = [{'id': 'a', 'email_address': 'alpha@example.com'}]

    assert apply_local_filters('contacts', rows, {'email': 'missing'}) == []
