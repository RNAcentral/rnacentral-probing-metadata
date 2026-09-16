#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "Missing dependency: pyyaml is required. Install with `pip install pyyaml`.\n"
    )
    raise


# Top-level ``comment`` prefixes that mark a dataset as excluded from the pipeline.
# Shared with merge_metadata.py so that skipped datasets are neither downloaded nor merged.
SKIP_COMMENT_PREFIXES = ("failed QC", "skip")


def skip_reason(data: dict) -> str | None:
    """Return the dataset comment if it marks the dataset as skipped, else None."""
    comment = str(data.get("comment") or "").strip()
    lowered = comment.lower()
    for prefix in SKIP_COMMENT_PREFIXES:
        if lowered.startswith(prefix.lower()):
            return comment
    return None


def extract_ids(data: dict) -> list[str]:
    """Extract run accessions from parsed YAML metadata."""
    if not isinstance(data, dict):
        raise ValueError("YAML top-level must be a mapping.")
    raw_data = data.get("raw_data")
    if not isinstance(raw_data, dict):
        raise ValueError("Metadata YAML is missing a 'raw_data' mapping.")
    run_accessions = raw_data.get("run_accessions")
    if not isinstance(run_accessions, list):
        raise ValueError("'raw_data.run_accessions' must be a list.")
    ids = []
    for i, item in enumerate(run_accessions):
        if not isinstance(item, dict):
            raise ValueError(f"run_accessions[{i}] must be a mapping, got {type(item).__name__}.")
        if "accession" not in item:
            raise ValueError(f"run_accessions[{i}] is missing the 'accession' key.")
        ids.append(str(item["accession"]).strip())
    return ids


def main() -> int:
    """Parse arguments, extract IDs from YAML, and write a one-per-line output file."""
    parser = argparse.ArgumentParser(
        description=(
            "Extract IDs from a YAML file and write to a single-column CSV file. "
            "Use raw_data.run_accessions[].accession values only. "
            "Datasets whose top-level comment starts with 'failed QC' or 'skip' "
            "produce no CSV, so they are never passed to fetchngs."
        )
    )
    parser.add_argument("yaml_path", help="Path to input YAML file")
    parser.add_argument("output_csv", help="Path to output CSV file")
    args = parser.parse_args()

    try:
        with open(args.yaml_path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ValueError(f"Failed to parse YAML file {args.yaml_path}: {exc}") from exc

    output_path = Path(args.output_csv)

    reason = skip_reason(data)
    if reason is not None:
        dataset_id = data.get("dataset_id", args.yaml_path)
        sys.stderr.write(f"Skipping {dataset_id}: {reason}\n")
        # Remove any CSV left over from before the dataset was marked as skipped,
        # otherwise RUN_FETCHNGS would still pick it up from the ids directory.
        if output_path.exists():
            output_path.unlink()
            sys.stderr.write(f"Removed stale {output_path}.\n")
        return 0

    ids = extract_ids(data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(ids))
        handle.write("\n")
    sys.stderr.write(f"Wrote {len(ids)} IDs to {output_path}.\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
