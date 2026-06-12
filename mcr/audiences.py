# # mcr/audiences.py
"""Audience operations for Mailchimp lists endpoints."""

from __future__ import annotations

from typing import Any

from mcr.client import MailchimpClient


def normalize_audience(item: dict[str, Any]) -> dict[str, Any]:
    """Normalize a Mailchimp list object into an audience row."""
    stats = item.get('stats', {})
    return {
        'id': item.get('id', ''),
        'name': item.get('name', ''),
        'member_count': stats.get('member_count', 0),
        'unsubscribe_count': stats.get('unsubscribe_count', 0),
    }


def list_audiences(
    client: MailchimpClient,
    limit: int,
    api_params: dict[str, Any] | None = None,
    audience_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Return normalized audience rows.
    Endpoint = '/lists'
    - uses 'lists' methods, 'audience' aligns with reporting naming convention
    """
    if audience_id:
        return [normalize_audience(client.get(f'lists/{audience_id}'))]

    lists = client.get_paginated(
        endpoint='lists',
        items_key='lists',
        limit=limit,
        params=api_params,
    )
    return [normalize_audience(item) for item in lists]


def resolve_audience_id(
    client: MailchimpClient,
    audience: str,
    limit: int = 1000,
) -> str:
    """Resolve an audience name to a non-empty Mailchimp list ID."""
    lists = client.get_paginated(
        endpoint='lists',
        items_key='lists',
        limit=limit,
        params=None,
    )
    matches = [
        item for item in lists
        if str(item.get('name', '')).casefold() == audience.casefold()
    ]

    if not matches:
        raise ValueError(f'No audience found with name {audience!r}.')
    if len(matches) > 1:
        raise ValueError(f'Multiple audiences found with name {audience!r}.')

    audience_id = str(matches[0].get('id') or '')
    if not audience_id:
        raise ValueError(f'Audience {audience!r} is missing an ID.')

    return audience_id
