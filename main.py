"""Command line interface for Mailchimp Marketing API read-only operations."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from mcr.audiences import list_audiences
from mcr.campaigns import list_campaigns
from mcr.client import MailchimpClient
from mcr.common import output_results
from mcr.contacts import list_contacts
from mcr.prompts import prompt_for_missing, VALID_REPORTS


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

    campaigns_parser = subparsers.add_parser('campaigns', help='List campaigns')
    add_common_args(campaigns_parser)
    campaigns_parser.add_argument('--limit', type=int)

    contacts_parser = subparsers.add_parser(
        'contacts',
        help='List contacts in audience',
    )
    add_common_args(contacts_parser)
    contacts_parser.add_argument('--limit', type=int)
    contacts_parser.add_argument('--audience-id')

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


def execute_report(args: argparse.Namespace) -> list[dict[str, Any]]:
    """
    Execute selected report and return normalized rows.
    """
    client = MailchimpClient(config_path=args.config)
    client.validate_connection()

    if args.report == 'audiences':
        return list_audiences(
            client=client,
            limit=args.limit,
            )

    if args.report == 'campaigns':
        return list_campaigns(
            client=client,
            limit=args.limit,
            )

    if args.report == 'contacts':
        return list_contacts(
            client=client,
            audience_id=args.audience_id,
            limit=args.limit,
        )

    raise ValueError('Unknown report requested')


def main() -> None:
    argv = sys.argv[1:]

    pre_parser = build_pre_parser()
    pre_args, remaining = pre_parser.parse_known_args(argv)

    report = detect_report(remaining)
    prompted_args: argparse.Namespace | None = None

    if not report:
        prompted_args = argparse.Namespace(
            report=None,
            config=pre_args.config,
            output=pre_args.output,
            savefile=pre_args.savefile,
            limit=None,
            audience_id=None,
        )
        prompted_args = prompt_for_missing(prompted_args)
        report = prompted_args.report

        remaining = normalize_report_argv(remaining, report)

        if report == 'contacts' and prompted_args.audience_id:
            if '--audience-id' not in remaining:
                remaining.extend(['--audience-id', prompted_args.audience_id])
    else:
        remaining = normalize_report_argv(remaining, report)

    parser = build_parser()
    args = parser.parse_args(remaining)

    if pre_args.config is not None:
        args.config = pre_args.config
    if pre_args.output is not None:
        args.output = pre_args.output
    if pre_args.savefile is not None:
        args.savefile = pre_args.savefile

    if prompted_args is not None:
        if getattr(args, 'config', None) is None:
            args.config = prompted_args.config
        if getattr(args, 'output', None) is None:
            args.output = prompted_args.output
        if getattr(args, 'savefile', None) is None:
            args.savefile = prompted_args.savefile
        if getattr(args, 'limit', None) is None:
            args.limit = prompted_args.limit
        if (
            getattr(args, 'report', None) == 'contacts'
            and getattr(args, 'audience_id', None) is None
        ):
            args.audience_id = prompted_args.audience_id

    if prompted_args is None:
        args = prompt_for_missing(args)

    rows = execute_report(args)
    output_results(
        rows=rows,
        output_format=args.output,
        report=args.report,
        savefile=args.savefile,
    )


if __name__ == '__main__':
    main()
