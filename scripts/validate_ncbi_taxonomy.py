#!/usr/bin/env python3
"""Validate organism.ncbi_taxid against NCBI Taxonomy and require strain for viral datasets."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import yaml


VIRAL_ORGANISMS = {
    "Influenza A virus",
    "SARS-CoV-2",
    "Zika virus",
    "HIV",
    "Rotavirus A",
}

# Organisms whose common name in this repo differs from NCBI Taxonomy's scientific name.
NCBI_ORGANISM_ALIASES = {
    "SARS-CoV-2": "Severe acute respiratory syndrome coronavirus 2",
    "HIV": "Human immunodeficiency virus 1",
}

NCBI_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
NCBI_MAX_ATTEMPTS = 5
NCBI_RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


class NcbiTaxonomyLookupError(RuntimeError):
    """Raised when NCBI Taxonomy cannot be queried reliably."""


def ncbi_retry_delay_seconds(exc: HTTPError | URLError | OSError, attempt: int) -> float:
    """Return delay before retrying an NCBI request."""
    if isinstance(exc, HTTPError):
        retry_after = exc.headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), 60.0)
            except ValueError:
                pass
    return min(2.0**attempt, 30.0)


def names_match(expected: str, actual: str) -> bool:
    """Return True if the metadata organism name matches the NCBI Taxonomy name.

    Accepts an exact match, a known common-name alias (e.g. SARS-CoV-2), or the
    NCBI name being a more specific strain-qualified form of the expected name
    (e.g. "Parasynechococcus marenigrum" matching NCBI's strain-level taxon
    "Parasynechococcus marenigrum WH 8102").
    """
    expected_norm = expected.strip().lower()
    actual_norm = actual.strip().lower()
    if expected_norm == actual_norm:
        return True
    alias = NCBI_ORGANISM_ALIASES.get(expected.strip())
    if alias and alias.strip().lower() == actual_norm:
        return True
    return actual_norm.startswith(f"{expected_norm} ")


def fetch_taxonomy_name(taxid: str) -> str | None:
    """Return the NCBI Taxonomy scientific name for a taxid, or None if it doesn't exist."""
    query = {"db": "taxonomy", "id": taxid, "retmode": "json"}
    url = f"{NCBI_ESUMMARY_URL}?{urlencode(query)}"
    request = Request(url, headers={"User-Agent": "rnacentral-probing-metadata-validator"})

    for attempt in range(1, NCBI_MAX_ATTEMPTS + 1):
        try:
            with urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except HTTPError as exc:
            can_retry = exc.code in NCBI_RETRY_STATUS_CODES
            if can_retry and attempt < NCBI_MAX_ATTEMPTS:
                time.sleep(ncbi_retry_delay_seconds(exc, attempt))
                continue
            raise NcbiTaxonomyLookupError(
                f"lookup for taxid '{taxid}' failed with HTTP {exc.code}: {exc.reason}"
            ) from exc
        except (TimeoutError, URLError, OSError) as exc:
            if attempt < NCBI_MAX_ATTEMPTS:
                time.sleep(ncbi_retry_delay_seconds(exc, attempt))
                continue
            raise NcbiTaxonomyLookupError(f"lookup for taxid '{taxid}' failed: {exc}") from exc

    result = data.get("result", {})
    entry = result.get(str(taxid))
    if not entry or not entry.get("scientificname"):
        return None
    return entry["scientificname"]


TaxonomyFetch = Callable[[str], "str | None"]


def validate_metadata_file(
    path: Path,
    fetch: TaxonomyFetch = fetch_taxonomy_name,
) -> list[str]:
    """Return NCBI Taxonomy validation issues for one YAML file."""
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except Exception as exc:
        return [f"{path}: failed to parse YAML ({exc})"]

    if not isinstance(data, dict):
        return [f"{path}: top-level YAML must be a mapping"]

    organism_data = data.get("organism") or {}
    if isinstance(organism_data, dict):
        organism = str(organism_data.get("scientific_name", "")).strip()
        taxid = str(organism_data.get("ncbi_taxid", "")).strip()
        strain = str(organism_data.get("strain", "")).strip()
    else:
        organism = str(organism_data).strip()
        taxid = ""
        strain = ""

    issues: list[str] = []
    if organism in VIRAL_ORGANISMS and not strain:
        issues.append(f"{path}: viral organism '{organism}' requires organism.strain")

    if not taxid or not taxid.isdigit():
        issues.append(f"{path}: organism.ncbi_taxid must be a plain integer, got '{taxid}'")
        return issues

    try:
        resolved_name = fetch(taxid)
    except NcbiTaxonomyLookupError as exc:
        issues.append(f"{path}: NCBI Taxonomy lookup failed for ncbi_taxid '{taxid}': {exc}")
        return issues

    if resolved_name is None:
        issues.append(f"{path}: ncbi_taxid '{taxid}' does not exist in NCBI Taxonomy")
        return issues

    if not names_match(organism, resolved_name):
        issues.append(
            f"{path}: organism '{organism}' does not match NCBI Taxonomy name "
            f"'{resolved_name}' for ncbi_taxid '{taxid}'"
        )

    return issues


def validate_metadata_files(
    paths: list[Path],
    fetch: TaxonomyFetch = fetch_taxonomy_name,
) -> list[str]:
    """Return validation issues across all provided YAML files."""
    issues: list[str] = []
    cache: dict[str, "str | None"] = {}

    def cached_fetch(taxid: str) -> "str | None":
        if taxid not in cache:
            cache[taxid] = fetch(taxid)
        return cache[taxid]

    for path in paths:
        issues.extend(validate_metadata_file(path, fetch=cached_fetch))
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("yamls", nargs="+", type=Path, help="Metadata YAML files to validate")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues = validate_metadata_files(args.yamls)
    if issues:
        print("NCBI Taxonomy validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print(f"NCBI Taxonomy validation passed for {len(args.yamls)} metadata file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
