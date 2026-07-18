#!/usr/bin/env python3
"""Expand a study accession into ENA run records for a metadata YAML.

Given a GEO series (GSExxxxx) or an SRA/ENA project (PRJNAxxxxx / PRJEBxxxxx),
resolve the underlying project and print, per run:
    run_accession  sample_accession  sample_title  experiment_title

This is the mechanical half of building `raw_data.run_accessions`; a human still
maps sample titles to condition (treated/untreated/denatured), sample_group and
replicate. No LLM, only the public GEO and ENA APIs.

Usage:
    python scripts/expand_accession.py GSE237160
    python scripts/expand_accession.py PRJNA1094587 --tsv
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request

GEO = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"
ENA = "https://www.ebi.ac.uk/ena/portal/api/filereport"


def get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def geo_to_project(gse: str) -> str:
    txt = get(f"{GEO}?acc={gse}&targ=self&form=text&view=full")
    m = re.search(r"BioProject.*?(PRJ[A-Z]+\d+)", txt)
    if not m:
        raise SystemExit(f"No BioProject found for {gse}")
    return m.group(1)


def ena_runs(project: str) -> list[list[str]]:
    fields = "run_accession,sample_accession,sample_title,experiment_title"
    url = (f"{ENA}?accession={project}&result=read_run&fields={fields}"
           f"&format=tsv")
    rows = [line.split("\t") for line in get(url).splitlines()]
    return rows[1:] if rows else []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("accession", help="GSExxxxx, PRJNAxxxxx or PRJEBxxxxx")
    ap.add_argument("--tsv", action="store_true", help="raw TSV instead of aligned")
    args = ap.parse_args()

    acc = args.accession.strip()
    project = geo_to_project(acc) if acc.upper().startswith("GSE") else acc
    print(f"# project: {project}", file=sys.stderr)
    rows = ena_runs(project)
    print(f"# runs: {len(rows)}", file=sys.stderr)
    for r in rows:
        r = (r + ["", "", "", ""])[:4]
        if args.tsv:
            print("\t".join(r))
        else:
            print(f"{r[0]:14} {r[1]:14} {r[2][:45]:45} {r[3][:45]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
