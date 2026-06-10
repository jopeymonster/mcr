# # mcr/audiences.py
"""Audience operations for Mailchimp lists endpoints."""

from __future__ import annotations

from typing import Any

from mcr.client import MailchimpClient


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
        audience = client.get(endpoint=f'lists/{audience_id}')
        stats = audience.get('stats', {})
        return [
            {
                'id': audience.get('id', ''),
                'name': audience.get('name', ''),
                'member_count': stats.get('member_count', 0),
                'unsubscribe_count': stats.get('unsubscribe_count', 0),
            }
        ]

    lists = client.get_paginated(
        endpoint='lists',
        items_key='lists',
        limit=limit,
        params=api_params,
    )
    rows: list[dict[str, Any]] = []
    for item in lists:
        stats = item.get('stats', {})
        rows.append(
            {
                'id': item.get('id', ''),
                'name': item.get('name', ''),
                'member_count': stats.get('member_count', 0),
                'unsubscribe_count': stats.get('unsubscribe_count', 0),
            }
        )
    return rows
