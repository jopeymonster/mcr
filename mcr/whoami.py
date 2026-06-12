"""Account context helpers for the whoami report."""

from __future__ import annotations

from typing import Any

from mcr.client import MailchimpClient


def normalize_account_context(
    data: dict[str, Any],
    base_url: str = '',
) -> list[dict[str, Any]]:
    """Normalize Mailchimp root endpoint account context."""
    contact = data.get('contact') or {}
    account_id = data.get('account_id') or data.get('accountId') or data.get('id', '')
    login = data.get('login_id') or data.get('login_email') or data.get('email', '')
    role = data.get('role') or data.get('account_type', '')
    server_prefix = data.get('dc') or data.get('data_center', '')

    if not server_prefix and '.api.mailchimp.com' in base_url:
        server_prefix = base_url.split('://', 1)[-1].split('.', 1)[0]

    return [
        {
            'account_id': account_id,
            'account_name': data.get('account_name', ''),
            'login': login,
            'role': role,
            'server_prefix': server_prefix,
            'company': contact.get('company', ''),
            'first_name': contact.get('fname', ''),
            'last_name': contact.get('lname', ''),
        }
    ]


def whoami(
    client: MailchimpClient,
    root_data: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Fetch and normalize authenticated Mailchimp account context."""
    data = root_data if root_data is not None else client.validate_connection()
    return normalize_account_context(data, base_url=client.base_url)
