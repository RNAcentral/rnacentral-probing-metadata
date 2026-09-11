#!/usr/bin/env python3
"""Batch-find chemical-probing dataset candidates from Europe PMC.

Mechanical triage only — no LLM. For each year range it searches Europe PMC for
chemical-probing methods, drops papers whose DOI is already in the repo, and for
every remaining hit resolves open-access status + PMCID and (for open-access hits)
the study's own GEO/SRA/PRJNA accession from the full-text XML.

Output: a TSV to stdout with columns
    year_range  doi  pub_year  open_access  pmcid  accession  title
plus two summary blocks on stderr:
    - ACCESSIBLE candidates (open access, ready to expand into a YAML)
    - PAYWALLED candidates (flag for manual review — DOI list)

Usage:
    python scripts/find_probing_candidates.py                # default 4 ranges
    python scripts/find_probing_candidates.py --ranges 2024-2025 2025-2026
    python scripts/find_probing_candidates.py > candidates.tsv
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
REPO = Path.cwd()  # skill runs from repo root; DMS/ and SHAPE/ are here

# Broad-recall probing terms. Named methods, reagents, and generic phrases so
# method-innovation papers (e.g. nanopore PORE-cupine, new SHAPE/DMS variants) are
# caught, not just the established Illumina protocols. The whole OR-block is AND-ed
# with ABSTRACT:"RNA" in search() to drop non-RNA "SHAPE"/"DMS" false positives
# (ML/imaging papers, generic chemistry) while keeping recall high. Prefer adding a
# term here over missing a paper — noise is triaged out downstream.
QUERY_TERMS = [
    # SHAPE family
    'ABSTRACT:"SHAPE-MaP"', 'ABSTRACT:"SHAPE-seq"', 'ABSTRACT:"SHAPE probing"',
    'ABSTRACT:"SHAPE reagent"', 'ABSTRACT:"selective 2\'-hydroxyl acylation"',
    'ABSTRACT:"icSHAPE"', 'ABSTRACT:"smartSHAPE"', 'ABSTRACT:"SHALiPE"',
    'ABSTRACT:"ClickSHAPE"', 'ABSTRACT:"Nuc-SHAPE"',
    # DMS family
    'ABSTRACT:"DMS-MaPseq"', 'ABSTRACT:"DMS-seq"', 'ABSTRACT:"DMS-MaP"',
    'ABSTRACT:"DMS probing"', 'ABSTRACT:"dimethyl sulfate"',
    # other seq-based probing methods
    'ABSTRACT:"Structure-seq"', 'ABSTRACT:"NAI-MaP"', 'ABSTRACT:"PORE-cupine"',
    'ABSTRACT:"keth-seq"', 'ABSTRACT:"CIRS-seq"', 'ABSTRACT:"Mod-seq"',
    'ABSTRACT:"PARS"', 'ABSTRACT:"mutational profiling"',
    # reagents
    'ABSTRACT:"NAI-N3"', 'ABSTRACT:"1M7"', 'ABSTRACT:"2A3"', 'ABSTRACT:"5NIA"',
    'ABSTRACT:"NMIA"', 'ABSTRACT:"benzoyl cyanide"',
    # generic / outcome phrases
    'ABSTRACT:"chemical probing"', 'ABSTRACT:"RNA structure probing"',
    'ABSTRACT:"structure probing"', 'ABSTRACT:"RNA structurome"',
    'ABSTRACT:"in vivo RNA structure"', 'ABSTRACT:"transcriptome-wide RNA structure"',
    'KW:"RNA structure"',
]
ACC_RE = re.compile(r"GSE\d{4,}|PRJNA\d{4,}|SRP\d{5,}|PRJEB\d{4,}|E-MTAB-\d{3,}")


def get(url: str, tries: int = 3) -> bytes:
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                raise
            time.sleep(1.5 * (i + 1))
    raise RuntimeError("unreachable")


def existing_dois() -> set[str]:
    dois: set[str] = set()
    for d in ("DMS", "SHAPE"):
        for f in (REPO / d).glob("*.yaml"):
            for line in f.read_text().splitlines():
                s = line.strip()
                if s.startswith("doi:"):
                    dois.add(s.split(":", 1)[1].strip().lower())
    return dois


def search(year_from: int, year_to: int, page_size: int = 200) -> list[dict]:
    # AND ABSTRACT:"RNA" scopes the broad OR-block to RNA papers, dropping the
    # non-RNA "SHAPE"/"DMS" noise while keeping recall high.
    query = (f"({' OR '.join(QUERY_TERMS)}) AND ABSTRACT:\"RNA\" "
             f"AND (PUB_TYPE:\"Journal Article\")")
    params = {
        "query": query,
        "format": "json",
        "pageSize": str(page_size),
        "resultType": "lite",
        "cursorMark": "*",
    }
    # Europe PMC year filter via query is more reliable than a separate param.
    params["query"] += f" AND (FIRST_PDATE:[{year_from}-01-01 TO {year_to}-12-31])"
    out: list[dict] = []
    seen_cursor = None
    while True:
        url = f"{EPMC}/search?" + urllib.parse.urlencode(params)
        data = json.loads(get(url))
        out.extend(data.get("resultList", {}).get("result", []))
        nxt = data.get("nextCursorMark")
        if not nxt or nxt == seen_cursor:
            break
        seen_cursor = params["cursorMark"] = nxt
    return out


def resolve_accession(pmcid: str) -> str:
    """Grep the open-access full-text XML for the first data accession."""
    try:
        xml = get(f"{EPMC}/{pmcid}/fullTextXML").decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return ""
    # Prefer accessions near a "data availability" / "deposited" cue.
    m = re.search(r"(availability of data|data availability|deposited).{0,600}",
                  xml, re.I | re.S)
    window = m.group(0) if m else xml
    hit = ACC_RE.search(window) or ACC_RE.search(xml)
    return hit.group(0) if hit else ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ranges", nargs="+",
                    default=["2022-2023", "2023-2024", "2024-2025", "2025-2026"],
                    help="Year ranges like 2024-2025.")
    ap.add_argument("--no-accession", action="store_true",
                    help="Skip full-text accession resolution (faster, fewer calls).")
    args = ap.parse_args()

    have = existing_dois()
    print("year_range\tdoi\tpub_year\topen_access\tpmcid\taccession\ttitle")
    accessible: list[tuple[str, str, str]] = []   # (doi, accession, title)
    paywalled: list[tuple[str, str, str]] = []     # (doi, year, title)
    seen_doi: set[str] = set()

    for rng in args.ranges:
        yf, yt = (int(x) for x in rng.split("-"))
        for r in search(yf, yt):
            doi = (r.get("doi") or "").lower()
            if not doi or doi in have or doi in seen_doi:
                continue
            seen_doi.add(doi)
            oa = r.get("isOpenAccess") == "Y"
            pmcid = r.get("pmcid") or ""
            title = (r.get("title") or "").replace("\t", " ").strip()
            acc = ""
            if oa and pmcid and not args.no_accession:
                acc = resolve_accession(pmcid)
            print(f"{rng}\t{doi}\t{r.get('pubYear','')}\t"
                  f"{'Y' if oa else 'N'}\t{pmcid}\t{acc}\t{title}")
            if oa:
                accessible.append((doi, acc, title))
            else:
                paywalled.append((doi, r.get("pubYear", ""), title))

    def block(label: str, rows: list) -> None:
        print(f"\n### {label} ({len(rows)})", file=sys.stderr)
        for row in rows:
            print("  " + " | ".join(str(x) for x in row), file=sys.stderr)

    block("ACCESSIBLE (open access — ready to expand into YAML)",
          [(d, a or "NO-ACCESSION-FOUND", t[:80]) for d, a, t in accessible])
    block("PAYWALLED (flag for manual review)",
          [(d, y, t[:90]) for d, y, t in paywalled])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
