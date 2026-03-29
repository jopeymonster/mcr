# client.py
"""HTTP client for Mailchimp Marketing API requests."""

from __future__ import annotations

from typing import Any

import requests

from mcr.auth import extract_data_center, load_api_key


class MailchimpClient:
    """
    GET HTTP client object 
    for read-only API calls 
    compatible with Python 3.11+
    curated for used with Mailchimp API.

    Libraries:
        - Requests HTTP Library / 'requests'
        - Internal module for API key session registry / 'auth'
    
    Mailchimp specifications:
        - Session validation at root endpoint
        - Uses paginated GET API option until
        LIMIT parameter/argument or result exhaustion

    """

    def __init__(self, config_path: str) -> None:
        """Initialize client from auth config path
        curated for used with Mailchimp API.
        
        Supports JSON headers and response, 
        decodes into dictionary and 
        transforms into rows for each output control.

        Base API URL Endpoint (api key data center dependent '{dc}')
        - 'https://{dc}.api.mailchimp.com/3.0/'

        """
        self.api_key = load_api_key(config_path)
        dc = extract_data_center(self.api_key)
        self.base_url = f'https://{dc}.api.mailchimp.com/3.0/'
        self.session = requests.Session()
        self.session.auth = ('anystring', self.api_key)
        self.session.headers.update({'Accept': 'application/json'})
    
    def validate_connection(self) -> dict[str, Any]:
        """Validate API access with root endpoint request.
        """
        return self.get('')

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Perform GET request and return decoded dictionary response
        curated for used with Mailchimp API."""
        cleaned = endpoint.lstrip('/')
        url = f'{self.base_url}{cleaned}'
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = ''
            try:
                payload = response.json()
                title = payload.get('title', 'Mailchimp API error')
                message = payload.get('detail', '')
                status = payload.get('status', response.status_code)
                detail = f' (status={status}, title={title}, detail={message})'
            except ValueError:
                detail =f' (status={response.status_code}, body={response.text[:300]})'
            raise RuntimeError(f'Mailchimp GET failed for {url}{detail}') from exc
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
        """Fetch paginated endpoint until limit or API result exhaustion.
        """
        if limit <= 0:
            raise ValueError('limit must be greater than 0')
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
