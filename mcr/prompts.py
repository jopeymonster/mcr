# prompts.py
"""Interactive prompt helpers for missing CLI arguments."""

from __future__ import annotations

import argparse


VALID_COMMANDS = ['audiences', 'campaigns', 'contacts']


def prompt_for_missing(args: argparse.Namespace) -> argparse.Namespace:
    """Prompt for required missing arguments and return updated namespace."""
    if not getattr(args, 'command', None):
        choice = input('Choose command (audiences/campaigns/contacts): ').strip()
        while choice not in VALID_COMMANDS:
            choice = input('Invalid command. Choose audiences, campaigns, or contacts: ').strip()
        args.command = choice

    if args.command == 'contacts' and not getattr(args, 'list_id', None):
        list_id = input('Enter Mailchimp list ID: ').strip()
        while not list_id:
            list_id = input('List ID is required. Enter Mailchimp list ID: ').strip()
        args.list_id = list_id

    if not getattr(args, 'config', None):
        args.config = input('Enter path to auth config (default config/auth.json): ').strip()
        if not args.config:
            args.config = 'config/auth.json'

    if not getattr(args, 'limit', None):
        limit_input = input('Enter max results (default 100): ').strip()
        args.limit = int(limit_input) if limit_input else 100

    return args
