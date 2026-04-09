# # mcr/common.py
"""Output and formatting helpers for CLI responses."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def timestamp_string() -> str:
    """Return a compact timestamp string for filenames."""
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def append_timestamp(path: Path, timestamp: str) -> Path:
    """Append timestamp before the suffix, preserving the directory."""
    if path.suffix:
        return path.with_name(f'{path.stem}_{timestamp}{path.suffix}')
    return path.with_name(f'{path.name}_{timestamp}')


def generate_output_path(report: str, output_format: str, savefile: str | None = None) -> Path:
    """
    Generate output path in user home output directory.

    Args:
        report type (str): Report type name used for default file naming.
         - Options: 'audiences' / 'campaigns' / 'contacts'
        output_format (str): CSV or JSON.
        savefile (str | None): Optional path override

    Returns:
        Path: Output path for saving file.
    """
    base_dir = Path.home() / 'mcr_outputs'
    base_dir.mkdir(parents=True, exist_ok=True)

    extension = 'csv' if output_format == 'csv' else 'json'
    timestamp = timestamp_string()

    if savefile:
        candidate = Path(savefile)
        if candidate.suffix:
            candidate = append_timestamp(candidate, timestamp)
        else:
            candidate = candidate.with_name(f'{candidate.name}_{timestamp}.{extension}')

        if candidate.is_absolute():
            return candidate
        return base_dir / candidate

    filename = f'{report}_{timestamp}.{extension}'
    return base_dir / filename


def save_csv(rows: list[dict[str, Any]], path: Path) -> Path:
    """
    Save rows as CSV file.
    """
    if not rows:
        rows = [{'message': 'No records found'}]

    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    return path


def save_json(rows: list[dict[str, Any]], path: Path) -> Path:
    """
    Save rows as JSON file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        json.dump(rows, handle, indent=2)
    return path


def print_table(rows: list[dict[str, Any]]) -> None:
    """
    Print row data as plain text table.
    """
    if not rows:
        print('No records found')
        return

    headers = list(rows[0].keys())
    rendered_rows: list[list[str]] = []
    widths = [len(h) for h in headers]

    for row in rows:
        rendered = [str(row.get(h, '')) for h in headers]
        rendered_rows.append(rendered)
        widths = [max(widths[i], len(rendered[i])) for i in range(len(headers))]

    header_line = ' | '.join(headers[i].ljust(widths[i]) for i in range(len(headers)))
    divider = '-+-'.join('-' * widths[i] for i in range(len(headers)))

    print(header_line)
    print(divider)
    for rendered in rendered_rows:
        line = ' | '.join(rendered[i].ljust(widths[i]) for i in range(len(headers)))
        print(line)


def output_results(
    rows: list[dict[str, Any]],
    output_format: str,
    report: str,
    savefile: str | None,
) -> None:
    """
    Route output to CSV, JSON, or console table.
    """
    if output_format == 'table':
        if savefile:
            print('Output is to console, ignoring savefile')
        print_table(rows)
        return

    out_path = generate_output_path(
        report=report,
        output_format=output_format,
        savefile=savefile,
    )

    if output_format == 'json':
        save_json(rows, out_path)
    else:
        save_csv(rows, out_path)

    print(f'Saved output to {out_path}')
