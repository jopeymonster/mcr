"""Minimal build backend for this small pure-Python package."""

from __future__ import annotations

import base64
import csv
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

NAME = 'mcr'
VERSION = '0.1.0'
DIST_INFO = f'{NAME}-{VERSION}.dist-info'
ROOT = Path(__file__).parent.resolve()


def _metadata() -> str:
    """Return package metadata content."""
    return '\n'.join(
        [
            'Metadata-Version: 2.1',
            f'Name: {NAME}',
            f'Version: {VERSION}',
            'Summary: Mailchimp Marketing API read-only CLI prototype',
            'Requires-Python: >=3.11',
            'Requires-Dist: requests',
            'Provides-Extra: dev',
            'Requires-Dist: pytest; extra == "dev"',
            'Requires-Dist: ruff; extra == "dev"',
            '',
        ]
    )


def _wheel() -> str:
    """Return wheel metadata content."""
    return '\n'.join(
        [
            'Wheel-Version: 1.0',
            'Generator: mcr-build-backend',
            'Root-Is-Purelib: true',
            'Tag: py3-none-any',
            '',
        ]
    )


def _entry_points() -> str:
    """Return console script entry point metadata."""
    return '\n'.join(['[console_scripts]', 'mcr = mcr.main:main', ''])


def _hash(data: bytes) -> tuple[str, str]:
    """Return RECORD hash and size for wheel data."""
    digest = hashlib.sha256(data).digest()
    encoded = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')
    return f'sha256={encoded}', str(len(data))


def _write_wheel(path: Path, files: dict[str, bytes]) -> None:
    """Write a wheel archive with a generated RECORD file."""
    record_path = f'{DIST_INFO}/RECORD'
    rows: list[list[str]] = []

    with ZipFile(path, 'w', ZIP_DEFLATED) as wheel:
        for archive_path, data in sorted(files.items()):
            wheel.writestr(archive_path, data)
            digest, size = _hash(data)
            rows.append([archive_path, digest, size])

        rows.append([record_path, '', ''])
        record_lines: list[str] = []
        for row in rows:
            output = []
            class _Writer:
                def write(self, value: str) -> None:
                    output.append(value)
            csv.writer(_Writer(), lineterminator='\n').writerow(row)
            record_lines.append(''.join(output))
        wheel.writestr(record_path, ''.join(record_lines).encode('utf-8'))


def _base_files() -> dict[str, bytes]:
    """Return common wheel metadata files."""
    return {
        f'{DIST_INFO}/METADATA': _metadata().encode('utf-8'),
        f'{DIST_INFO}/WHEEL': _wheel().encode('utf-8'),
        f'{DIST_INFO}/entry_points.txt': _entry_points().encode('utf-8'),
    }


def build_wheel(
    wheel_directory: str,
    config_settings: dict[str, object] | None = None,
    metadata_directory: str | None = None,
) -> str:
    """Build a pure-Python wheel."""
    files = _base_files()
    for package_file in (ROOT / NAME).glob('*.py'):
        files[f'{NAME}/{package_file.name}'] = package_file.read_bytes()

    wheel_name = f'{NAME}-{VERSION}-py3-none-any.whl'
    _write_wheel(Path(wheel_directory) / wheel_name, files)
    return wheel_name


def build_editable(
    wheel_directory: str,
    config_settings: dict[str, object] | None = None,
    metadata_directory: str | None = None,
) -> str:
    """Build an editable wheel that adds the repository root to sys.path."""
    files = _base_files()
    files[f'{NAME}_editable.pth'] = f'{ROOT}\n'.encode('utf-8')

    wheel_name = f'{NAME}-{VERSION}-py3-none-any.whl'
    _write_wheel(Path(wheel_directory) / wheel_name, files)
    return wheel_name


def get_requires_for_build_wheel(
    config_settings: dict[str, object] | None = None,
) -> list[str]:
    """Return build requirements for regular wheels."""
    return []


def get_requires_for_build_editable(
    config_settings: dict[str, object] | None = None,
) -> list[str]:
    """Return build requirements for editable wheels."""
    return []


def prepare_metadata_for_build_wheel(
    metadata_directory: str,
    config_settings: dict[str, object] | None = None,
) -> str:
    """Prepare dist-info metadata for a wheel build."""
    dist_info = Path(metadata_directory) / DIST_INFO
    dist_info.mkdir(parents=True, exist_ok=True)
    (dist_info / 'METADATA').write_text(_metadata(), encoding='utf-8')
    (dist_info / 'WHEEL').write_text(_wheel(), encoding='utf-8')
    (dist_info / 'entry_points.txt').write_text(_entry_points(), encoding='utf-8')
    return DIST_INFO


def prepare_metadata_for_build_editable(
    metadata_directory: str,
    config_settings: dict[str, object] | None = None,
) -> str:
    """Prepare dist-info metadata for an editable build."""
    return prepare_metadata_for_build_wheel(metadata_directory, config_settings)
