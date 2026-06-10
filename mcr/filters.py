"""Local post-fetch filtering helpers."""

from __future__ import annotations

from typing import Any, Iterable


def _contains(value: Any, needle: str) -> bool:
    """Return true when value contains needle case-insensitively."""
    return needle.casefold() in str(value or '').casefold()


def _first_present(row: dict[str, Any], fields: Iterable[str]) -> list[Any]:
    """Collect present row values for the supplied field names."""
    return [row[field] for field in fields if row.get(field) is not None]


def filter_campaigns_by_subject(
    rows: list[dict[str, Any]],
    subject: str | None,
) -> list[dict[str, Any]]:
    """Filter campaign rows by subject or title fields."""
    if not subject:
        return rows

    fields = ('subject_line', 'title', 'campaign_title')
    return [
        row for row in rows
        if any(_contains(value, subject) for value in _first_present(row, fields))
    ]


def filter_contacts_by_email(
    rows: list[dict[str, Any]],
    email: str | None,
) -> list[dict[str, Any]]:
    """Filter contact rows by email address."""
    if not email:
        return rows

    return [
        row for row in rows
        if _contains(row.get('email_address'), email)
    ]


def filter_contacts_by_name(
    rows: list[dict[str, Any]],
    name: str | None,
) -> list[dict[str, Any]]:
    """Filter contact rows by available normalized name fields."""
    if not name:
        return rows

    fields = ('full_name', 'first_name', 'last_name', 'name')
    return [
        row for row in rows
        if any(_contains(value, name) for value in _first_present(row, fields))
    ]


def apply_local_filters(
    report: str,
    rows: list[dict[str, Any]],
    filters: dict[str, Any],
) -> list[dict[str, Any]]:
    """Apply supported local filters to normalized rows."""
    if report == 'campaigns':
        return filter_campaigns_by_subject(rows, filters.get('subject'))

    if report == 'contacts':
        filtered = filter_contacts_by_email(rows, filters.get('email'))
        return filter_contacts_by_name(filtered, filters.get('name'))

    return rows
