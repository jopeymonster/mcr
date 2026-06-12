"""Tests for report execution and audience resolution behavior."""

from __future__ import annotations

import argparse
import sys

import pytest

from mcr import main
from mcr.audiences import resolve_audience_id
from mcr.prompts import prompt_for_missing


class FakeClient:
    """Fake Mailchimp client for report tests."""

    def __init__(self, config_path: str = 'config/auth.json') -> None:
        self.config_path = config_path
        self.base_url = 'https://us7.api.mailchimp.com/3.0/'
        self.get_calls: list[tuple[str, dict[str, object] | None]] = []
        self.paginated_calls: list[tuple[str, str, int, dict[str, object] | None]] = []

    def validate_connection(self) -> dict[str, object]:
        """Return a fake root response."""
        return {
            'account_id': 'acct1',
            'account_name': 'Example Account',
            'login_id': 'owner@example.com',
            'role': 'owner',
        }

    def get(self, endpoint: str, params: dict[str, object] | None = None) -> dict[str, object]:
        """Return fake single endpoint responses."""
        self.get_calls.append((endpoint, params))
        if endpoint == 'lists/aud123':
            return {'id': 'aud123', 'name': 'Customers', 'stats': {'member_count': 2}}
        return {}

    def get_paginated(
        self,
        endpoint: str,
        items_key: str,
        limit: int,
        params: dict[str, object] | None = None,
        page_size: int = 100,
    ) -> list[dict[str, object]]:
        """Return fake paginated endpoint responses."""
        self.paginated_calls.append((endpoint, items_key, limit, params))
        if endpoint == 'lists':
            return [
                {'id': 'aud123', 'name': 'Customers', 'stats': {'member_count': 2}},
                {'id': 'aud456', 'name': 'Prospects', 'stats': {'member_count': 1}},
            ]
        if endpoint == 'lists/aud123/members':
            return [
                {
                    'id': 'mem1',
                    'email_address': 'ada@example.com',
                    'full_name': 'Ada Lovelace',
                    'merge_fields': {'FNAME': 'Ada', 'LNAME': 'Lovelace'},
                }
            ]
        if endpoint == 'campaigns':
            return [
                {'id': 'camp1', 'settings': {'subject_line': 'Spring Sale'}},
                {'id': 'camp2', 'settings': {'subject_line': 'Winter Sale'}},
            ]
        return []


def normalized_args(**values: object) -> dict[str, object]:
    """Build normalized args for execute report tests."""
    defaults: dict[str, object] = {
        'report': 'audiences',
        'config': 'config/auth.json',
        'output': 'json',
        'savefile': None,
        'limit': 100,
        'audience_id': None,
        'audience': None,
        'api_params': {'count': 100},
        'filters': {},
    }
    defaults.update(values)
    return defaults


def test_direct_audience_id_uses_single_audience_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Audiences report with audience ID should fetch lists by path."""
    fake = FakeClient()
    monkeypatch.setattr(main, 'MailchimpClient', lambda config_path: fake)

    rows = main.execute_report(
        normalized_args(audience_id='aud123', api_params={'count': 100})
    )

    assert rows == [
        {'id': 'aud123', 'name': 'Customers', 'member_count': 2, 'unsubscribe_count': 0}
    ]
    assert fake.get_calls == [('lists/aud123', None)]
    assert fake.paginated_calls == []


def test_audience_name_resolution_uses_single_audience_fetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Audiences report with a name should resolve once and fetch by path."""
    fake = FakeClient()
    monkeypatch.setattr(main, 'MailchimpClient', lambda config_path: fake)

    rows = main.execute_report(normalized_args(audience='Customers'))

    assert rows[0]['id'] == 'aud123'
    assert fake.paginated_calls == [('lists', 'lists', 1000, None)]
    assert fake.get_calls == [('lists/aud123', None)]


def test_no_audience_id_preserves_paginated_audiences_behavior(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Audiences report without audience ID should fetch paginated lists."""
    fake = FakeClient()
    monkeypatch.setattr(main, 'MailchimpClient', lambda config_path: fake)

    rows = main.execute_report(normalized_args())

    assert [row['id'] for row in rows] == ['aud123', 'aud456']
    assert fake.get_calls == []
    assert fake.paginated_calls == [('lists', 'lists', 100, {'count': 100})]


def test_campaign_audience_id_bypasses_name_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Campaign audience IDs should go directly to campaign API params."""
    fake = FakeClient()
    monkeypatch.setattr(main, 'MailchimpClient', lambda config_path: fake)

    rows = main.execute_report(
        normalized_args(
            report='campaigns',
            audience_id='aud123',
            api_params={'count': 100, 'list_id': 'aud123'},
        )
    )

    assert [row['id'] for row in rows] == ['camp1', 'camp2']
    assert fake.paginated_calls == [
        ('campaigns', 'campaigns', 100, {'count': 100, 'list_id': 'aud123'})
    ]


def test_campaign_audience_name_resolves_to_list_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Campaign audience names should resolve into list_id params."""
    fake = FakeClient()
    monkeypatch.setattr(main, 'MailchimpClient', lambda config_path: fake)

    rows = main.execute_report(
        normalized_args(
            report='campaigns',
            audience='Customers',
            api_params={'count': 100},
        )
    )

    assert [row['id'] for row in rows] == ['camp1', 'camp2']
    assert fake.paginated_calls == [
        ('lists', 'lists', 1000, None),
        ('campaigns', 'campaigns', 100, {'count': 100, 'list_id': 'aud123'}),
    ]


def test_audience_name_resolution_uses_resolved_id_for_contacts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Audience names should resolve before fetching contacts."""
    fake = FakeClient()
    monkeypatch.setattr(main, 'MailchimpClient', lambda config_path: fake)

    rows = main.execute_report(
        normalized_args(
            report='contacts',
            audience='Customers',
            api_params={'count': 100},
            filters={},
        )
    )

    assert rows[0]['email_address'] == 'ada@example.com'
    assert fake.paginated_calls == [
        ('lists', 'lists', 1000, None),
        ('lists/aud123/members', 'members', 100, {'count': 100}),
    ]


def test_direct_audience_id_for_contacts_skips_name_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Direct audience IDs should fetch contacts without resolving names."""
    fake = FakeClient()
    monkeypatch.setattr(main, 'MailchimpClient', lambda config_path: fake)

    rows = main.execute_report(
        normalized_args(
            report='contacts',
            audience_id='aud123',
            api_params={'count': 100},
            filters={},
        )
    )

    assert rows[0]['email_address'] == 'ada@example.com'
    assert fake.paginated_calls == [
        ('lists/aud123/members', 'members', 100, {'count': 100})
    ]


def test_audience_name_does_not_prompt_when_supplied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prompt helper should not ask for audience ID when audience name exists."""
    args = argparse.Namespace(
        report='contacts',
        audience='Customers',
        audience_id=None,
        config='config/auth.json',
        output='table',
        savefile=None,
        limit=100,
    )
    monkeypatch.setattr('builtins.input', lambda prompt='': pytest.fail(prompt))

    prompted = prompt_for_missing(args)

    assert prompted.audience == 'Customers'
    assert prompted.audience_id is None


def test_resolve_audience_id_rejects_missing_id() -> None:
    """Audience name resolution should reject matches without an ID."""
    fake = FakeClient()

    def missing_id_paginated(
        endpoint: str,
        items_key: str,
        limit: int,
        params: dict[str, object] | None = None,
        page_size: int = 100,
    ) -> list[dict[str, object]]:
        return [{'name': 'Customers'}]

    fake.get_paginated = missing_id_paginated  # type: ignore[method-assign]

    with pytest.raises(ValueError, match='missing an ID'):
        resolve_audience_id(fake, 'Customers')


def test_resolve_audience_id_rejects_multiple_matches() -> None:
    """Audience name resolution should reject duplicate names."""
    fake = FakeClient()

    def duplicate_paginated(
        endpoint: str,
        items_key: str,
        limit: int,
        params: dict[str, object] | None = None,
        page_size: int = 100,
    ) -> list[dict[str, object]]:
        return [{'id': 'a', 'name': 'Customers'}, {'id': 'b', 'name': 'Customers'}]

    fake.get_paginated = duplicate_paginated  # type: ignore[method-assign]

    with pytest.raises(ValueError, match='Multiple audiences'):
        resolve_audience_id(fake, 'Customers')


def test_whoami_uses_root_context_without_audience(monkeypatch: pytest.MonkeyPatch) -> None:
    """Whoami should normalize root endpoint context without audience input."""
    fake = FakeClient()
    monkeypatch.setattr(main, 'MailchimpClient', lambda config_path: fake)

    rows = main.execute_report(
        normalized_args(report='whoami', limit=None, api_params={}, filters={})
    )

    assert rows == [
        {
            'account_id': 'acct1',
            'account_name': 'Example Account',
            'login': 'owner@example.com',
            'role': 'owner',
            'server_prefix': 'us7',
            'company': '',
            'first_name': '',
            'last_name': '',
        }
    ]
    assert fake.get_calls == []
    assert fake.paginated_calls == []


def test_campaign_subject_filter_is_post_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Subject filtering should not change campaign API params."""
    fake = FakeClient()
    monkeypatch.setattr(main, 'MailchimpClient', lambda config_path: fake)

    rows = main.execute_report(
        normalized_args(
            report='campaigns',
            api_params={'count': 100},
            filters={'subject': 'spring'},
        )
    )

    assert [row['id'] for row in rows] == ['camp1']
    assert fake.paginated_calls == [('campaigns', 'campaigns', 100, {'count': 100})]


def run_cli_smoke(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
) -> tuple[FakeClient, list[dict[str, object]]]:
    """Run the CLI entry flow with a fake client and captured rows."""
    fake = FakeClient()
    captured: list[dict[str, object]] = []
    monkeypatch.setattr(sys, 'argv', argv)
    monkeypatch.setattr(main, 'MailchimpClient', lambda config_path: fake)

    def capture_output(
        rows: list[dict[str, object]],
        output_format: str,
        report: str,
        savefile: str | None,
    ) -> None:
        captured.extend(rows)

    monkeypatch.setattr(main, 'output_results', capture_output)
    main.main()
    return fake, captured


def test_cli_smoke_audiences(monkeypatch: pytest.MonkeyPatch) -> None:
    """The audiences CLI path should build, execute, and output rows."""
    fake, rows = run_cli_smoke(
        monkeypatch,
        ['mcr', 'audiences', '--config', 'auth.json', '--output', 'table', '--limit', '2'],
    )

    assert [row['id'] for row in rows] == ['aud123', 'aud456']
    assert fake.paginated_calls[0][0] == 'lists'


def test_cli_smoke_campaigns(monkeypatch: pytest.MonkeyPatch) -> None:
    """The campaigns CLI path should build, execute, and output rows."""
    fake, rows = run_cli_smoke(
        monkeypatch,
        ['mcr', 'campaigns', '--config', 'auth.json', '--output', 'table', '--limit', '2'],
    )

    assert [row['id'] for row in rows] == ['camp1', 'camp2']
    assert fake.paginated_calls[0][0] == 'campaigns'


def test_cli_smoke_contacts(monkeypatch: pytest.MonkeyPatch) -> None:
    """The contacts CLI path should build, execute, and output rows."""
    fake, rows = run_cli_smoke(
        monkeypatch,
        [
            'mcr',
            'contacts',
            '--config',
            'auth.json',
            '--output',
            'table',
            '--limit',
            '2',
            '--audience-id',
            'aud123',
        ],
    )

    assert rows[0]['email_address'] == 'ada@example.com'
    assert fake.paginated_calls[0][0] == 'lists/aud123/members'


def test_cli_smoke_whoami(monkeypatch: pytest.MonkeyPatch) -> None:
    """The whoami CLI path should build, execute, and output root context."""
    fake, rows = run_cli_smoke(
        monkeypatch,
        ['mcr', 'whoami', '--config', 'auth.json', '--output', 'table'],
    )

    assert rows[0]['account_id'] == 'acct1'
    assert fake.get_calls == []
    assert fake.paginated_calls == []
