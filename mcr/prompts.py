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

    if args.command == 'contacts' and not getattr(args, 'audience_id', None):
        audience_id = input('Enter Mailchimp audience ID: ').strip()
        while not audience_id:
            audience_id = input(
                'Audience ID is required. Enter Mailchimp audience ID: '
            ).strip()
        args.audience_id = audience_id

    return args
