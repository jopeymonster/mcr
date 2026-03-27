# client.py
"""HTTP client for Mailchimp Marketing API requests."""

from __future__ import annotations

from typing import Any

import requests

from mcr.auth import extract_data_center, load_api_key


class MailchimpClient:
    """Minimal Mailchimp HTTP client for read-only API calls."""

    def __init__(self, config_path: str) -> None:
        """Initialize client from auth config path."""
        self.api_key = load_api_key(config_path)
        dc = extract_data_center(self.api_key)
        self.base_url = f'https://{dc}.api.mailchimp.com/3.0/'
        self.session = requests.Session()
        self.session.auth = ('anystring', self.api_key)
        self.session.headers.update({'Accept': 'application/json'})

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Perform GET request and return decoded JSON response."""
        cleaned = endpoint.lstrip('/')
        url = f'{self.base_url}{cleaned}'
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(f'Mailchimp GET failed for {url}: {exc}') from exc

        try:
            return response.json()
        except ValueError as exc:
            raise RuntimeError('Mailchimp response was not valid JSON') from exc

    def get_paginated(
        self,
        endpoint: str,
        items_key: str,
        limit: int,
        params: dict[str, Any] | None = None,
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch paginated endpoint until limit or API result exhaustion."""
        records: list[dict[str, Any]] = []
        offset = 0
        query = params.copy() if params else {}

        while len(records) < limit:
            batch_size = min(page_size, limit - len(records))
            query.update({'count': batch_size, 'offset': offset})
            data = self.get(endpoint=endpoint, params=query)
            page_items = data.get(items_key, [])
            if not page_items:
                break

            records.extend(page_items)
            offset += len(page_items)
            if len(page_items) < batch_size:
                break

        return records[:limit]
