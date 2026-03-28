# main.py
"""Command line interface for Mailchimp Marketing API read-only operations."""

from __future__ import annotations

import argparse
from typing import Any

from mcr.audiences import list_audiences
from mcr.campaigns import list_campaigns
from mcr.client import MailchimpClient
from mcr.common import output_results
from mcr.contacts import list_contacts
from mcr.prompts import prompt_for_missing


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description='Read-only CLI tool for Mailchimp Marketing API'
    )
    parser.add_argument('--config', default='config/auth.json')
    parser.add_argument('--output', choices=['csv', 'json', 'table'], default='csv')
    parser.add_argument('--savefile')
    parser.add_argument('--limit', type=int, default=100)

    subparsers = parser.add_subparsers(dest='command')

    subparsers.add_parser('audiences', help='List audiences')
    subparsers.add_parser('campaigns', help='List campaigns')

    contacts_parser = subparsers.add_parser('contacts', help='List contacts in audience')
    contacts_parser.add_argument('--audience-id')

    return parser


def execute_command(args: argparse.Namespace) -> list[dict[str, Any]]:
    """Execute selected command and return normalized rows."""
    client = MailchimpClient(config_path=args.config)
    client.validate_connection()

    if args.command == 'audiences':
        return list_audiences(client=client, limit=args.limit)

    if args.command == 'campaigns':
        return list_campaigns(client=client, limit=args.limit)

    if args.command == 'contacts':
        return list_contacts(
            client=client, 
            audience_id=args.audience_id,
            limit=args.limit,
        )

    raise ValueError('Unknown command requested')


def main() -> None:
    """CLI application entry point."""
    parser = build_parser()
    args = parser.parse_args()
    args = prompt_for_missing(args)

    rows = execute_command(args)
    output_results(
        rows=rows,
        output_format=args.output,
        command=args.command,
        savefile=args.savefile,
    )


if __name__ == '__main__':
    main()
