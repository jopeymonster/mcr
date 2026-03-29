# campaigns.py
"""Campaign operations for Mailchimp campaigns endpoint."""

from __future__ import annotations

from typing import Any

from mcr.client import MailchimpClient


def list_campaigns(client: MailchimpClient, limit: int) -> list[dict[str, Any]]:
    """Return normalized campaign rows."""
    campaigns = client.get_paginated(
        endpoint='campaigns', 
        items_key='campaigns', 
        limit=limit,
    )
    rows: list[dict[str, Any]] = []
    for item in campaigns:
        rows.append(
            {
                'id': item.get('id', ''),
                'status': item.get('status', ''),
                'type': item.get('type', ''),
                'emails_sent': item.get('emails_sent', 0),
                'subject_line': item.get('settings', {}).get('subject_line', ''),
                'send_time': item.get('send_time', ''),
            }
        )
    return rows
