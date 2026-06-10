"""Tests for client pagination helpers."""

from __future__ import annotations

from typing import Any

from mcr.client import MailchimpClient


class PagingClient(MailchimpClient):
    """Client subclass with fake GET responses."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return fake pages and record query params."""
        query = dict(params or {})
        self.calls.append(query)
        offset = query['offset']
        count = query['count']
        items = [{'id': str(index)} for index in range(offset, offset + count)]
        return {'items': items}


def test_get_paginated_uses_limit_for_count_and_offsets() -> None:
    """Pagination should request count and offset until the limit is reached."""
    client = PagingClient()

    rows = client.get_paginated('things', 'items', limit=5, page_size=2)

    assert [row['id'] for row in rows] == ['0', '1', '2', '3', '4']
    assert client.calls == [
        {'count': 2, 'offset': 0},
        {'count': 2, 'offset': 2},
        {'count': 1, 'offset': 4},
    ]
