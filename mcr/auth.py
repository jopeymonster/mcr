# auth.py
"""Authentication helpers for Mailchimp API access."""

from __future__ import annotations

import json
from pathlib import Path


def load_api_key(config_path: str) -> str:
    """Load Mailchimp API key from JSON config file.

    Args:
        config_path (str): Path to JSON file containing API credentials.

    Returns:
        str: Mailchimp API key.

    Raises:
        FileNotFoundError: If config file is missing.
        ValueError: If API key field is missing or empty.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f'Config file not found: {config_path}')

    with path.open('r', encoding='utf-8') as handle:
        payload = json.load(handle)

    api_key = payload.get('api_key')
    if api_key is None:
        api_key = payload.get('mailchimp_api_key')
    if api_key == "YOUR_API_KEY":
        raise ValueError('Placeholder key found in config file')
    
    if not api_key:
        raise ValueError('Missing api_key in config file')

    return api_key


def extract_data_center(api_key: str) -> str:
    """Extract Mailchimp data center from API key.

    Args:
        api_key (str): Mailchimp key in format token-dc.

    Returns:
        str: Data center string.

    Raises:
        ValueError: If API key format is invalid.
    """
    parts = api_key.split('-')
    if len(parts) < 2 or not parts[-1]:
        raise ValueError('Invalid Mailchimp API key format: expected token-data_center')
    return parts[-1]
