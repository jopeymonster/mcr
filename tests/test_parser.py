"""Tests for CLI parser construction."""

from __future__ import annotations

from mcr.main import build_parser


def test_parser_builds_repeatedly_without_duplicate_option_conflicts() -> None:
    """Parser construction should not register duplicate options."""
    build_parser()
    build_parser()


def test_parser_accepts_report_specific_arguments() -> None:
    """Report parsers should accept the intended v0.1 options."""
    parser = build_parser()

    audiences = parser.parse_args(['audiences', '--audience-id', 'aud123'])
    campaigns = parser.parse_args(['campaigns', '--audience', 'Customers', '--subject', 'sale'])
    contacts = parser.parse_args(['contacts', '--audience', 'Customers', '--email', 'ada'])
    whoami = parser.parse_args(['whoami', '--config', 'auth.json'])

    assert audiences.report == 'audiences'
    assert audiences.audience_id == 'aud123'
    assert campaigns.subject == 'sale'
    assert contacts.email == 'ada'
    assert whoami.report == 'whoami'
    assert whoami.config == 'auth.json'


def test_whoami_parser_does_not_require_audience_or_date_args() -> None:
    """Whoami should parse without audience or date arguments."""
    parsed = build_parser().parse_args(['whoami'])

    assert parsed.report == 'whoami'
    assert not hasattr(parsed, 'audience_id')
    assert not hasattr(parsed, 'start_date')


def test_root_help_exits_without_prompt(monkeypatch) -> None:
    """Root help should render parser help without entering prompts."""
    import sys

    import pytest

    from mcr import main

    monkeypatch.setattr(sys, 'argv', ['mcr', '--help'])
    monkeypatch.setattr('builtins.input', lambda prompt='': pytest.fail(prompt))

    with pytest.raises(SystemExit) as excinfo:
        main.main()

    assert excinfo.value.code == 0
