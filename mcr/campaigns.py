# # mcr/campaigns.py
"""Campaign operations for Mailchimp campaigns endpoint."""

from __future__ import annotations

from typing import Any

from mcr.client import MailchimpClient


def list_campaigns(
        client: MailchimpClient, 
        limit: int,
        api_params: dict[str, Any] | None = None,
        ) -> list[dict[str, Any]]:
    """
    Return normalized campaign rows.
    Endpoint = '/campaigns'
    - campaigns supports audience_id --> list_id as a query parameter
    """
    campaigns = client.get_paginated(
        endpoint='campaigns', 
        items_key='campaigns', 
        limit=limit,
        params=api_params,
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
