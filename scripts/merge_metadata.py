#!/usr/bin/env python3
"""Build a pipeline samplesheet from fetchngs CSV + dataset YAML.

Output format:
sample,sample_id,fastq_1,fastq_2,method,principle,chemical,RT_enzyme,sample_group,
condition,replicate,organism,pH,adapter_3p,adapter_5p,umi_pattern

Datasets whose top-level comment starts with "failed QC" are skipped entirely.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import yaml


VIRAL_ORGANISMS = {
    "Influenza A virus",
    "SARS-CoV-2",
    "Zika virus",
    "HIV",
    "Rotavirus A",
}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for metadata merge inputs and output path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--samplesheet", required=True, help="Path to fetchngs samplesheet CSV"
    )
    parser.add_argument(
        "--metadata", required=True, help="Path to manual dataset metadata YAML"
    )
    parser.add_argument(
        "--out",
        help="Output samplesheet CSV path. Default: <dataset_id>_samplesheet.csv",
    )
    return parser.parse_args()


def read_yaml(path: Path) -> dict:
    """Load metadata YAML and ensure the top-level object is a mapping."""
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ValueError(f"Failed to parse YAML file {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Metadata YAML must be a mapping: {path}")
    return data


def extract_run_metadata_map(metadata: dict) -> dict[str, dict[str, str]]:
    """Map accession IDs to per-sample metadata."""
    raw_data = metadata.get("raw_data")
    if not isinstance(raw_data, dict):
        raise ValueError("Metadata YAML is missing a 'raw_data' mapping.")
    run_accessions = raw_data.get("run_accessions")
    if not isinstance(run_accessions, list):
        raise ValueError("'raw_data.run_accessions' must be a list.")

    result = {}
    for item in run_accessions:
        accession = str(item["accession"]).strip()
        result[accession] = {
            "sample_name": str(item["sample_name"]).strip(),
            "sample_group": str(item.get("sample_group", "")).strip(),
            "condition": str(item.get("condition", "")).strip(),
            "replicate": str(item.get("replicate", "")).strip(),
        }
    return result


ACCESSION_MATCH_COLUMNS = (
    "sample_alias",
    "experiment_accession",
    "run_accession",
    "sample_accession",
    "secondary_sample_accession",
    "experiment_alias",
    "run_alias",
    "sample",
    "library_name",  # GEO: newer records store GSM ID here; secondary_sample_accession is SRS
)


def row_match_candidates(row: dict[str, str]) -> list[str]:
    """Return fetchngs row values that may correspond to a curated accession."""
    candidates = []
    seen = set()
    for column in ACCESSION_MATCH_COLUMNS:
        value = (row.get(column) or "").strip()
        if value and value not in seen:
            candidates.append(value)
            seen.add(value)
    return candidates


def find_run_metadata(
    row: dict[str, str], run_metadata_map: dict[str, dict[str, str]]
) -> tuple[str | None, dict[str, str] | None]:
    """Match a fetchngs row to curated metadata using any available accession column."""
    for candidate in row_match_candidates(row):
        run_metadata = run_metadata_map.get(candidate)
        if run_metadata:
            return candidate, run_metadata
    return None, None


DMS_CHEMICAL = "DMS"


def normalize_method(chemical: str) -> str:
    """Return 'DMS' if chemical is DMS, otherwise 'SHAPE' for any other ChemicalEnum value."""
    if chemical.strip() == DMS_CHEMICAL:
        return "DMS"
    return "SHAPE"


def extract_organism_name(metadata: dict) -> str:
    """Return samplesheet organism name, including viral strain when present."""
    organism = metadata.get("organism")
    if isinstance(organism, dict):
        organism_name = str(organism.get("scientific_name", "")).strip()
    elif isinstance(organism, str):
        organism_name = organism.strip()
    else:
        organism_name = ""

    strain = str((organism.get("strain", "") if isinstance(organism, dict) else "")).strip()
    if organism_name in VIRAL_ORGANISMS and strain:
        return f"{organism_name} ({strain})"
    return organism_name


def _build_out_row(
    run_accession: str,
    run_metadata: dict[str, str],
    fetchngs_row: dict[str, str],
    experiment: dict,
    method: str,
    organism: str,
) -> dict[str, str]:
    return {
        "sample": run_metadata["sample_name"],
        "sample_id": run_accession,
        "fastq_1": fetchngs_row.get("fastq_1", ""),
        "fastq_2": fetchngs_row.get("fastq_2", ""),
        "method": method,
        "principle": experiment.get("principle", ""),
        "chemical": experiment.get("chemical", ""),
        "RT_enzyme": experiment.get("RT_enzyme", ""),
        "sample_group": run_metadata["sample_group"],
        "condition": run_metadata["condition"],
        "replicate": run_metadata["replicate"],
        "organism": organism,
        "pH": experiment.get("pH", ""),
        "adapter_3p": experiment.get("adapter_3p", ""),
        "adapter_5p": experiment.get("adapter_5p", ""),
        "umi_pattern": experiment.get("umi_pattern", ""),
    }


def main() -> int:
    """Merge fetchngs samplesheet rows with dataset metadata and write output CSV."""
    args = parse_args()
    samplesheet_path = Path(args.samplesheet)
    metadata_path = Path(args.metadata)
    out_path: Path | None = Path(args.out) if args.out else None

    with samplesheet_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Empty samplesheet: {samplesheet_path}")

    metadata = read_yaml(metadata_path)
    dataset_id = metadata.get("dataset_id", str(metadata_path))
    dataset_comment = str(metadata.get("comment") or "")
    if dataset_comment.startswith("failed QC"):
        print(
            f"Skipping {dataset_id}: {dataset_comment}",
            file=sys.stderr,
        )
        return 0

    run_metadata_map = extract_run_metadata_map(metadata)
    dataset_id = metadata.get("dataset_id", "")
    experiment = metadata.get("experiment") or {}
    organism = extract_organism_name(metadata)
    method = normalize_method(experiment.get("chemical", ""))

    if out_path is None:
        if dataset_id:
            out_path = metadata_path.parent / f"{dataset_id}_samplesheet.csv"
        else:
            out_path = metadata_path.parent / "merged_samplesheet.csv"

    out_rows = []
    missing_accessions = []
    for row in rows:
        run_accession, run_metadata = find_run_metadata(row, run_metadata_map)
        if run_accession is None or run_metadata is None:
            alias = (row.get("sample_alias") or row.get("sample") or "<unknown>").strip()
            missing_accessions.append(alias)
            continue
        out_rows.append(
            _build_out_row(run_accession, run_metadata, row, experiment, method, organism)
        )

    if missing_accessions:
        n = len(missing_accessions)
        joined = ", ".join(missing_accessions)
        print(
            f"WARNING: {n} fetchngs row(s) had no matching YAML accession"
            f" and were skipped: {joined}",
            file=sys.stderr,
        )

    if not out_rows:
        raise ValueError("No rows produced. Check run_accessions and fetchngs IDs.")

    fieldnames = [
        "sample",
        "sample_id",
        "fastq_1",
        "fastq_2",
        "method",
        "principle",
        "chemical",
        "RT_enzyme",
        "sample_group",
        "condition",
        "replicate",
        "organism",
        "pH",
        "adapter_3p",
        "adapter_5p",
        "umi_pattern",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
