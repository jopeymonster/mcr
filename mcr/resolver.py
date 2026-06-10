# # mcr/resolver.py
"""Resolver helpers for mapping user input to concrete Mailchimp resources."""

from __future__ import annotations

from typing import Any

from mcr.client import MailchimpClient


def get_list_rows(client: MailchimpClient) -> list[dict[str, Any]]:
    """
    Fetch all audience list rows once for in-memory resolution.

    Args:
        client (MailchimpClient): Initialized Mailchimp API client.

    Returns:
        list[dict[str, Any]]: Raw audience rows from the lists endpoint.
    """
    response = client.get(endpoint='lists', params={'count': 1000, 'offset': 0})
    return response.get('lists', [])


def resolve_audience(
    client: MailchimpClient,
    normalized_args: dict[str, Any],
) -> dict[str, Any]:
    """
    Resolve audience input into audience_id when possible.

    Args:
        client (MailchimpClient): Initialized Mailchimp API client.
        normalized_args (dict[str, Any]): Normalized CLI argument state.

    Returns:
        dict[str, Any]: Updated normalized args.

    Raises:
        ValueError: If required audience input is missing or ambiguous.
    """
    report = normalized_args.get('report')
    audience_id = normalized_args.get('audience_id')
    audience_name = normalized_args.get('audience')

    if report == 'contacts' and not audience_id and not audience_name:
        raise ValueError(
            'Contacts report requires --audience-id or --audience.'
        )

    if audience_id:
        return normalized_args

    if not audience_name:
        return normalized_args

    lists = get_list_rows(client)

    exact_matches = [row for row in lists if row.get('name') == audience_name]
    if len(exact_matches) == 1:
        normalized_args['audience_id'] = exact_matches[0].get('id')
        return normalized_args
    if len(exact_matches) > 1:
        ids = ', '.join(match.get('id', '') for match in exact_matches)
        raise ValueError(
            f'Multiple audiences matched name: {audience_name}. Matching IDs: {ids}'
        )

    lower_target = audience_name.lower()
    ci_matches = [
        row for row in lists if str(row.get('name', '')).lower() == lower_target
    ]
    if len(ci_matches) == 1:
        normalized_args['audience_id'] = ci_matches[0].get('id')
        return normalized_args
    if len(ci_matches) > 1:
        ids = ', '.join(match.get('id', '') for match in ci_matches)
        raise ValueError(
            f'Multiple audiences matched name: {audience_name}. Matching IDs: {ids}'
        )

    raise ValueError(f'No audience found matching name: {audience_name}')
