# mcr/args.py
"""Argument normalization and API parameter mapping helpers."""

from __future__ import annotations

import argparse
from typing import Any


API_PARAM_MAP: dict[str, dict[str, str]] = {
    'campaigns': {
        'limit': 'count',
        'audience_id': 'list_id',
        # Date parameter placeholders
        # 'start_date': 'since_send_time',
        # 'end_date': 'before_send_time',
    },
    'audiences': {
        'limit': 'count',
        # Date parameter placeholders
        'start_date': 'since_date_created',
        'end_date': 'before_date_created',
    },
    'contacts': {
        'limit': 'count',
        # Date parameter placeholders
        'start_date': 'since_timestamp_opt',
        'end_date': 'before_timestamp_opt',
    },
}


def build_api_params(normalized_args: dict[str, Any]) -> dict[str, Any]:
    """
    Build query parameters for supported Mailchimp endpoints.

    Args:
        normalized_args (dict[str, Any]): Normalized arguments dictionary.

    Returns:
        dict[str, Any]: Query parameter dictionary for the active scope.
    """
    report = normalized_args.get('report')
    if not report or report not in API_PARAM_MAP:
        return {}

    param_map = API_PARAM_MAP[report]
    api_params: dict[str, Any] = {}

    if normalized_args.get('limit') is not None and 'limit' in param_map:
        api_params[param_map['limit']] = normalized_args['limit']

    if report == 'campaigns' and normalized_args.get('audience_id') is not None:
        audience_key = param_map.get('audience_id')
        if audience_key:
            api_params[audience_key] = normalized_args['audience_id']

    return {key: value for key, value in api_params.items() if value is not None}


def normalize_args(args: argparse.Namespace) -> dict[str, Any]:
    """
    Normalize parsed argparse values into a stable execution structure.

    Args:
        args (argparse.Namespace): Parsed CLI arguments.

    Returns:
        dict[str, Any]: Normalized arguments with API params and local filters.
    """
    normalized: dict[str, Any] = {
        'report': getattr(args, 'report', None),
        'config': getattr(args, 'config', None),
        'output': getattr(args, 'output', None),
        'savefile': getattr(args, 'savefile', None),
        'limit': getattr(args, 'limit', None),
        'audience_id': getattr(args, 'audience_id', None),
        'audience': getattr(args, 'audience', None),
        'api_params': {},
        'filters': {},
    }

    normalized['api_params'] = build_api_params(normalized)
    return normalized