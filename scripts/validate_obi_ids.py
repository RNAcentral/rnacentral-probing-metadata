#!/usr/bin/env python3
"""Validate experiment chemical to OBI ID mappings in metadata YAML files."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


EXPECTED_OBI_BY_CHEMICAL = {
    "DMS": "OBI:0001015",
    "NMIA": "OBI:0001026",
    "1M7": "OBI:0003885",
    "NAI": "OBI:0003886",
    "NAI-N3": "OBI:0003887",
    "2A3": "OBI:0003888",
    "1M6": "OBI:0003895",
    "5NIA": "OBI:0003896",
}


def clean_scalar(value: object) -> str:
    """Return a stripped string for present scalar values, or empty for null."""
    if value is None:
        return ""
    return str(value).strip()


def validate_metadata_file(path: Path) -> list[str]:
    """Return OBI validation issues for one YAML metadata file."""
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except Exception as exc:
        return [f"{path}: failed to parse YAML ({exc})"]

    if not isinstance(data, dict):
        return [f"{path}: top-level YAML must be a mapping"]

    experiment = data.get("experiment")
    if not isinstance(experiment, dict):
        return [f"{path}: missing or invalid experiment"]

    chemical = clean_scalar(experiment.get("chemical"))
    if not chemical:
        return [f"{path}: missing experiment.chemical"]

    expected_obi = EXPECTED_OBI_BY_CHEMICAL.get(chemical)
    if expected_obi is None:
        return [f"{path}: no OBI mapping configured for chemical '{chemical}'"]

    obi = clean_scalar(experiment.get("obi"))
    if not obi:
        return [f"{path}: chemical '{chemical}' requires experiment.obi '{expected_obi}'"]

    if obi != expected_obi:
        return [
            f"{path}: chemical '{chemical}' expects experiment.obi '{expected_obi}', "
            f"found '{obi}'"
        ]

    return []


def validate_metadata_files(paths: list[Path]) -> list[str]:
    """Return OBI validation issues across all provided YAML metadata files."""
    issues: list[str] = []
    for path in paths:
        issues.extend(validate_metadata_file(path))
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("yamls", nargs="+", type=Path, help="Metadata YAML files to validate")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues = validate_metadata_files(args.yamls)
    if issues:
        print("OBI ID validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print(f"OBI ID validation passed for {len(args.yamls)} metadata file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
