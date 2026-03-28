# audiences.py
"""Audience operations for Mailchimp lists endpoints."""

from __future__ import annotations

from typing import Any

from mcr.client import MailchimpClient


def list_audiences(client: MailchimpClient, limit: int) -> list[dict[str, Any]]:
    """Return normalized audience rows."""
    lists = client.get_paginated(endpoint='lists', items_key='lists', limit=limit)
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
