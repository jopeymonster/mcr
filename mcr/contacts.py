# # mcr/contacts.py
"""Contact operations for Mailchimp list members endpoint."""

from __future__ import annotations

from typing import Any

from mcr.client import MailchimpClient


def list_contacts(
        client: MailchimpClient, 
        audience_id: str, 
        limit: int,
    ) -> list[dict[str, Any]]:
    """
    Return normalized contact rows for a given audience list.
    Endpoint = 'lists/{audience_id}/members'
    - audience_id for contacts is path-based list_id input
    """
    members = client.get_paginated(
        endpoint=f'lists/{audience_id}/members',
        items_key='members',
        limit=limit,
    )
    rows: list[dict[str, Any]] = []
    for item in members:
        rows.append(
            {
                'id': item.get('id', ''),
                'email_address': item.get('email_address', ''),
                'status': item.get('status', ''),
                'full_name': item.get('full_name', ''),
                'member_rating': item.get('member_rating', 0),
                'last_changed': item.get('last_changed', ''),
            }
        )
    return rows
