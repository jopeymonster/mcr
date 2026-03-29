"""Interactive prompt helpers for missing CLI arguments."""

from __future__ import annotations

import argparse


VALID_REPORTS = ['audiences', 'campaigns', 'contacts']
FILE_OUTPUTS = {'csv', 'json'}


def prompt_for_missing(args: argparse.Namespace) -> argparse.Namespace:
    """
    Prompt for required missing arguments and return updated namespace.
    """
    if not hasattr(args, 'report'):
        args.report = None
    if not hasattr(args, 'config'):
        args.config = None
    if not hasattr(args, 'output'):
        args.output = None
    if not hasattr(args, 'savefile'):
        args.savefile = None
    if not hasattr(args, 'limit'):
        args.limit = None
    if not hasattr(args, 'audience_id'):
        args.audience_id = None

    if not args.report:
        choice = input('Choose report type (audiences/campaigns/contacts): ').strip()
        while choice not in VALID_REPORTS:
            choice = input(
                'Invalid report. Choose audiences, campaigns, or contacts: '
            ).strip()
        args.report = choice

    if args.report == 'contacts' and not args.audience_id:
        audience_id = input('Enter Mailchimp audience ID: ').strip()
        while not audience_id:
            audience_id = input(
                'Audience ID is required. Enter Mailchimp audience ID: '
            ).strip()
        args.audience_id = audience_id

    if not args.config:
        config_input = input(
            'Enter path to auth config [config/auth.json]: '
        ).strip()
        args.config = config_input or 'config/auth.json'

    if not args.output:
        output_input = input(
            'Select output format [csv/json/table] (default csv): '
        ).strip().lower()
        while output_input and output_input not in {'csv', 'json', 'table'}:
            output_input = input(
                'Invalid output. Choose csv, json, or table (default csv): '
            ).strip().lower()
        args.output = output_input or 'csv'

    if args.limit is None and args.report in {'audiences', 'campaigns', 'contacts'}:
        limit_input = input('Enter max results [100]: ').strip()
        while limit_input:
            try:
                parsed_limit = int(limit_input)
                if parsed_limit <= 0:
                    raise ValueError
                args.limit = parsed_limit
                break
            except ValueError:
                limit_input = input(
                    'Invalid limit. Enter a positive integer [100]: '
                ).strip()
        if args.limit is None:
            args.limit = 100

    if args.output in FILE_OUTPUTS:
        if args.savefile is None:
            savefile_input = input(
                'Enter savefile name/path or press Enter for auto-generated name: '
            ).strip()
            args.savefile = savefile_input or None
    else:
        args.savefile = None

    return args