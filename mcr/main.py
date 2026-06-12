# mcr/main.py
"""
Command line interface for Mailchimp Marketing API read-only operations.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from mcr.args import normalize_args
from mcr.audiences import list_audiences, resolve_audience_id
from mcr.campaigns import list_campaigns
from mcr.client import MailchimpClient
from mcr.common import output_results
from mcr.contacts import list_contacts
from mcr.filters import apply_local_filters
from mcr.prompts import VALID_REPORTS, prompt_for_missing
from mcr.whoami import whoami


def build_pre_parser() -> argparse.ArgumentParser:
    """
    Build parser for universal args that may appear without a report scope.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--config')
    parser.add_argument('--output', choices=['csv', 'json', 'table'])
    parser.add_argument('--savefile')
    return parser


def add_common_args(parser: argparse.ArgumentParser) -> None:
    """
    Add common args to a report parser.
    """
    parser.add_argument('--config')
    parser.add_argument('--output', choices=['csv', 'json', 'table'])
    parser.add_argument('--savefile')
    parser.add_argument('--start-date')
    parser.add_argument('--end-date')
    parser.add_argument('--last', type=int)
    parser.add_argument(
        '--previous',
        choices=['week', 'month', 'quarter', 'year'],
        help='Use a completed named period before the current one.',
    )


def build_parser() -> argparse.ArgumentParser:
    """
    Build the full report scope parser.
    """
    parser = argparse.ArgumentParser(
        description='Read-only CLI tool for Mailchimp Marketing API',
    )
    subparsers = parser.add_subparsers(dest='report')

    audiences_parser = subparsers.add_parser('audiences', help='List audiences')
    add_common_args(audiences_parser)
    audiences_parser.add_argument('--limit', type=int)
    audiences_parser.add_argument('--audience-id')
    audiences_parser.add_argument('--audience')

    campaigns_parser = subparsers.add_parser('campaigns', help='List campaigns')
    add_common_args(campaigns_parser)
    campaigns_parser.add_argument('--limit', type=int)
    campaigns_parser.add_argument('--audience-id')
    campaigns_parser.add_argument('--audience')
    campaigns_parser.add_argument('--subject')

    contacts_parser = subparsers.add_parser(
        'contacts',
        help='List contacts in audience',
    )
    add_common_args(contacts_parser)
    contacts_parser.add_argument('--limit', type=int)
    contacts_parser.add_argument('--audience-id')
    contacts_parser.add_argument('--audience')
    contacts_parser.add_argument('--email')
    contacts_parser.add_argument('--name')

    whoami_parser = subparsers.add_parser('whoami', help='Show account context')
    whoami_parser.add_argument('--config')
    whoami_parser.add_argument('--output', choices=['csv', 'json', 'table'])
    whoami_parser.add_argument('--savefile')

    return parser


def detect_report(tokens: list[str]) -> str | None:
    """
    Return the first recognized report token, if present.
    """
    for token in tokens:
        if token in VALID_REPORTS:
            return token
    return None


def normalize_report_argv(tokens: list[str], report: str) -> list[str]:
    """
    Rebuild argv to eliminate parsing scope errors.
    """
    reordered: list[str] = []
    report_removed = False

    for token in tokens:
        if not report_removed and token == report:
            report_removed = True
            continue
        reordered.append(token)

    return [report] + reordered


def build_prompt_namespace(pre_args: argparse.Namespace) -> argparse.Namespace:
    """Build default values used before interactive prompting."""
    return argparse.Namespace(
        report=None,
        config=pre_args.config,
        output=pre_args.output,
        savefile=pre_args.savefile,
        limit=None,
        audience_id=None,
        audience=None,
        subject=None,
        email=None,
        name=None,
        start_date=None,
        end_date=None,
        last=None,
        previous=None,
    )


def apply_pre_args(args: argparse.Namespace, pre_args: argparse.Namespace) -> None:
    """Apply pre-parser values to the report parser namespace."""
    for field in ('config', 'output', 'savefile'):
        value = getattr(pre_args, field, None)
        if value is not None:
            setattr(args, field, value)


def apply_prompted_args(
    args: argparse.Namespace,
    prompted_args: argparse.Namespace | None,
) -> None:
    """Fill missing parsed values from prior prompted values."""
    if prompted_args is None:
        return

    for field in (
        'config',
        'output',
        'savefile',
        'limit',
        'audience_id',
        'audience',
        'subject',
        'email',
        'name',
        'start_date',
        'end_date',
        'last',
        'previous',
    ):
        if getattr(args, field, None) is None:
            setattr(args, field, getattr(prompted_args, field, None))


def execute_report(normalized_args: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Execute selected report and return normalized rows.
    """
    client = MailchimpClient(config_path=normalized_args['config'])
    root_data = client.validate_connection()

    if normalized_args['report'] == 'whoami':
        return whoami(client=client, root_data=root_data)

    if normalized_args.get('audience') and not normalized_args.get('audience_id'):
        normalized_args['audience_id'] = resolve_audience_id(
            client=client,
            audience=normalized_args['audience'],
        )
        if normalized_args['report'] == 'campaigns':
            normalized_args['api_params']['list_id'] = normalized_args['audience_id']

    if normalized_args['report'] == 'audiences':
        return list_audiences(
            client=client,
            limit=normalized_args['limit'],
            api_params=normalized_args['api_params'],
            audience_id=normalized_args['audience_id'],
        )

    if normalized_args['report'] == 'campaigns':
        rows = list_campaigns(
            client=client,
            limit=normalized_args['limit'],
            api_params=normalized_args['api_params'],
        )
        return apply_local_filters(
            report='campaigns',
            rows=rows,
            filters=normalized_args['filters'],
        )

    if normalized_args['report'] == 'contacts':
        rows = list_contacts(
            client=client,
            audience_id=normalized_args['audience_id'],
            limit=normalized_args['limit'],
            api_params=normalized_args['api_params'],
        )
        return apply_local_filters(
            report='contacts',
            rows=rows,
            filters=normalized_args['filters'],
        )

    raise ValueError('Unknown report requested')


def main() -> None:
    argv = sys.argv[1:]

    pre_parser = build_pre_parser()
    pre_args, remaining = pre_parser.parse_known_args(argv)

    report = detect_report(remaining)
    prompted_args: argparse.Namespace | None = None

    if not report and any(token in {'-h', '--help'} for token in remaining):
        build_parser().parse_args(remaining)
        return

    if not report:
        prompted_args = prompt_for_missing(build_prompt_namespace(pre_args))
        report = prompted_args.report
        remaining = normalize_report_argv(remaining, report)

        if report == 'contacts' and prompted_args.audience_id:
            if '--audience-id' not in remaining:
                remaining.extend(['--audience-id', prompted_args.audience_id])
    else:
        remaining = normalize_report_argv(remaining, report)

    parser = build_parser()
    args = parser.parse_args(remaining)

    apply_pre_args(args, pre_args)
    apply_prompted_args(args, prompted_args)

    if prompted_args is None:
        args = prompt_for_missing(args)

    normalized_args = normalize_args(args)
    rows = execute_report(normalized_args)
    output_results(
        rows=rows,
        output_format=normalized_args['output'],
        report=normalized_args['report'],
        savefile=normalized_args['savefile'],
    )


if __name__ == '__main__':
    main()
