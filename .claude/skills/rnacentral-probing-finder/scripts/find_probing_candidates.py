#!/usr/bin/env python3
"""Batch-find chemical-probing dataset candidates from Europe PMC.

Mechanical triage only — no LLM. For each year range it searches Europe PMC for
chemical-probing methods, drops papers whose DOI is already in the repo, and for
every remaining hit resolves open-access status + PMCID and the study's own
GEO/SRA/PRJNA accession: open-access full text first, then Europe PMC text-mined
annotations, then NCBI's PubMed -> GEO links, then a BioProject whose title matches
the paper's.

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
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
ANNOTATIONS = "https://www.ebi.ac.uk/europepmc/annotations_api/annotationsByArticleIds"
REPO = Path.cwd()  # skill runs from repo root; DMS/ and SHAPE/ are here
EXCLUDED = Path(__file__).resolve().parent.parent / "excluded_dois.tsv"

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
ACC_RE = re.compile(r"GSE\d{4,}|PRJNA\d{4,}|SRP\d{5,}|PRJEB\d{4,}|PRJDB\d{4,}|DR[AP]\d{6,}|E-MTAB-\d{3,}")
# Experiment / run ids. Text mining often catches only these (e.g. SRX554885 for
# PRJNA248760), so they are mapped back to their study through ENA.
RUN_RE = re.compile(r"[SED]R[XR]\d{6,}")
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


# NCBI allows 3 requests/s per IP, 10 with a (free) API key. Every NCBI call goes
# through get(), which spaces them out and backs off on 429 instead of giving up:
# an unthrottled all-years sweep got rate-limited for hours and silently lost hits.
NCBI_KEY = os.environ.get("NCBI_API_KEY", "")
NCBI_GAP = 0.12 if NCBI_KEY else 0.4
_ncbi_last = 0.0
FAILED: dict[str, int] = {}  # host -> requests that failed for good (reported at the end)


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def get(url: str, tries: int = 3) -> bytes:
    global _ncbi_last
    ncbi = url.startswith(EUTILS)
    if ncbi and NCBI_KEY:
        url += "&api_key=" + NCBI_KEY
    failures = throttled = 0
    while True:
        if ncbi:
            time.sleep(max(0.0, _ncbi_last + NCBI_GAP - time.monotonic()))
            _ncbi_last = time.monotonic()
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and throttled < 6:
                throttled += 1
                ra = e.headers.get("Retry-After", "")
                time.sleep(float(ra) if ra.isdigit() else min(60, 5 * 2 ** (throttled - 1)))
                continue
            failures += 1
            err: Exception = e
        except Exception as e:  # noqa: BLE001
            failures += 1
            err = e
        if failures >= tries:
            if tries > 1:  # single-try calls (Europe PMC full text) have a fallback
                host = urllib.parse.urlparse(url).netloc
                FAILED[host] = FAILED.get(host, 0) + 1
            raise err
        time.sleep(1.5 * failures)


def existing_dois() -> set[str]:
    dois: set[str] = set()
    for d in ("DMS", "SHAPE"):
        for f in (REPO / d).glob("*.yaml"):
            for line in f.read_text().splitlines():
                s = line.strip()
                if s.startswith("doi:"):
                    dois.add(s.split(":", 1)[1].strip().lower())
    # Papers already triaged and rejected (scope / replicates / not RNA), so a
    # sweep does not surface them again. Append a row when you reject one.
    if EXCLUDED.exists():
        for line in EXCLUDED.read_text().splitlines()[1:]:
            doi = line.split("\t", 1)[0].strip().lower()
            if doi:
                dois.add(doi)
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


# Cues for the paper's OWN deposit, strongest first. Methods sections also name
# reused data ("obtained from a previous study (GSE103421)"), so the first
# accession in the text is often someone else's.
CUES = [re.compile(c, re.I) for c in (
    r"data availability|availability of data|data and code availability",
    r"accession (?:number|code)s?|deposited|have been submitted|are available (?:at|in|from)",
)]


def full_text(pmcid: str, oa: bool) -> str:
    """Full-text XML: Europe PMC for open access, else NCBI PMC.

    Europe PMC 500s on author manuscripts and other non-OA PMC records, but NCBI
    efetch still serves their body (6 of 7 non-OA papers in the benchmark).
    """
    urls = [f"{EUTILS}/efetch.fcgi?db=pmc&id={pmcid}&retmode=xml"]
    if oa:
        urls.insert(0, f"{EPMC}/{pmcid}/fullTextXML")
    for url in urls:
        try:
            xml = get(url, tries=1 if "europepmc" in url else 3).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            continue
        if "<body" in xml:
            return xml
    return ""


STOP = {"the", "and", "for", "with", "from", "into", "that", "this", "their", "reveals",
        "reveal", "using", "analysis", "study", "role", "via"}


def title_words(title: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", title.lower()) if len(w) > 2 and w not in STOP]


def bioproject_by_title(title: str, year: str) -> str:
    """BioProject whose title matches the paper's (submitters often reuse it).

    Catches deposits nothing links to the paper (e.g. PRJEB28648, Zika Cell Host &
    Microbe 2018: no PMC copy, no GEO, no annotation). Accepts only a close title
    match registered no later than the year after publication: generic titles
    ("Influenza A Virus genome structure", 2024) otherwise match older papers.
    """
    words = title_words(title)
    if len(words) < 4:
        return ""
    term = " AND ".join(words[:6])
    try:
        ids = json.loads(get(f"{EUTILS}/esearch.fcgi?" + urllib.parse.urlencode(
            {"db": "bioproject", "retmode": "json", "retmax": "20", "term": term})))["esearchresult"]["idlist"]
        if not ids:
            return ""
        summ = json.loads(get(f"{EUTILS}/esummary.fcgi?" + urllib.parse.urlencode(
            {"db": "bioproject", "retmode": "json", "id": ",".join(ids)})))["result"]
    except Exception:  # noqa: BLE001
        return ""
    want = set(words)
    best, score = "", 0.0
    for u in ids:
        reg = summ.get(u, {}).get("registration_date", "")[:4]
        if year.isdigit() and reg.isdigit() and int(reg) > int(year) + 1:
            continue
        got = set(title_words(summ.get(u, {}).get("project_title", "")))
        j = len(want & got) / len(want | got) if got else 0.0
        if j > score:
            best, score = summ[u]["project_acc"], j
    return best if score >= 0.6 else ""


def accession_in(xml: str) -> str:
    """The study's own accession in a full text: first hit after the strongest cue."""
    text = re.sub(r"<[^>]+>", " ", xml)
    for cue in CUES:
        for m in cue.finditer(text):
            if hit := ACC_RE.search(text, m.start(), m.end() + 600):
                return hit.group(0)
    hit = ACC_RE.search(text)
    return hit.group(0) if hit else ""


def accessions_from_annotations(pmcids: list[str]) -> dict[str, str]:
    """Text-mined accessions for up to 8 PMCIDs, via the Europe PMC annotations API.

    This is the ONLY angle that works for author-manuscript / non-open-access
    records: `fullTextXML` 500s or is withheld for them, but Europe PMC still
    text-mines the deposited text and exposes the accessions here. It is also the
    only angle that worked for the paper that motivated it (Cell 2026 norovirus,
    PMC13586799 -> GSE310315), where pubmed->gds elink returned nothing too.

    Results come back in arbitrary order, so key on each record's own `pmcid`
    field - never on the request order.
    """
    if not pmcids:
        return {}
    q = urllib.parse.urlencode({
        "articleIds": ",".join("PMC:" + p for p in pmcids[:8]),
        "type": "Accession Numbers",
        "format": "JSON",
    })
    try:
        data = json.loads(get(f"{ANNOTATIONS}?{q}"))
    except Exception:  # noqa: BLE001
        return {}
    out: dict[str, str] = {}
    runs: dict[str, str] = {}
    for art in data:
        pmc = art.get("pmcid") or ""
        for a in art.get("annotations", []):
            exact = (a.get("exact") or "").strip()
            if pmc and ACC_RE.fullmatch(exact):
                out.setdefault(pmc, exact)
            elif pmc and RUN_RE.fullmatch(exact):
                runs.setdefault(pmc, exact)
    # Study-level ids win; fall back to the study of a mined experiment/run id.
    for pmc, run in runs.items():
        if pmc not in out and (study := study_of_run(run)):
            out[pmc] = study
    return out


def study_of_run(run: str) -> str:
    """ENA study (PRJ...) holding an experiment or run id, or '' if unknown."""
    try:
        tsv = get("https://www.ebi.ac.uk/ena/portal/api/filereport?" + urllib.parse.urlencode(
            {"accession": run, "result": "read_run", "fields": "study_accession",
             "format": "tsv", "limit": "1"})).decode()
    except Exception:  # noqa: BLE001
        return ""
    lines = tsv.splitlines()
    return lines[1].split("\t")[-1].strip() if len(lines) > 1 else ""


def geo_series_from_pubmed(pmids: list[str]) -> dict[str, str]:
    """GEO series linked to each PMID (comma-joined), via NCBI elink pubmed -> gds.

    Curated links, so it is precise and found every GEO-deposited paper in the
    hand-curated benchmark; but GEO only (blind to SRA/ENA-only data) and it lags
    publication by weeks to months. Multiple series (SuperSeries + subseries, or
    reused data) are all returned for the curator to pick from.
    """
    if not pmids:
        return {}
    q = urllib.parse.urlencode([("dbfrom", "pubmed"), ("db", "gds"), ("retmode", "json")]
                               + [("id", p) for p in pmids])
    try:
        data = json.loads(get(f"{EUTILS}/elink.fcgi?{q}"))
    except Exception:  # noqa: BLE001
        return {}
    out: dict[str, str] = {}
    for ls in data.get("linksets", []):
        uids = [u for d in ls.get("linksetdbs", []) for u in d.get("links", [])]
        # GEO uids encode the type: 200000000 + n is series GSEn (GDS/GSM/GPL differ).
        gse = [f"GSE{int(u) - 200000000}" for u in uids if len(u) == 9 and u.startswith("200")]
        if gse:
            out[ls["ids"][0]] = ",".join(gse)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ranges", nargs="+",
                    default=["2022-2023", "2023-2024", "2024-2025", "2025-2026"],
                    help="Year ranges like 2024-2025.")
    ap.add_argument("--no-accession", action="store_true",
                    help="Skip accession resolution (faster, fewer calls).")
    args = ap.parse_args()

    have = existing_dois()
    print("year_range\tdoi\tpub_year\topen_access\tpmcid\taccession\ttitle")
    accessible: list[tuple[str, str, str]] = []   # (doi, accession, title)
    paywalled: list[tuple[str, str, str]] = []     # (doi, year, title)
    recovered: list[tuple[str, str, str]] = []     # paywalled, but accession text-mined
    seen_doi: set[str] = set()

    rows: list[dict] = []
    for rng in args.ranges:
        yf, yt = (int(x) for x in rng.split("-"))
        hits = search(yf, yt)
        log(f"search {rng}: {len(hits)} hits")
        for r in hits:
            doi = (r.get("doi") or "").lower()
            if not doi or doi in have or doi in seen_doi:
                continue
            seen_doi.add(doi)
            rows.append({
                "rng": rng, "doi": doi, "year": r.get("pubYear", ""),
                "oa": r.get("isOpenAccess") == "Y", "pmcid": r.get("pmcid") or "",
                "pmid": r.get("pmid") or "",
                "title": (r.get("title") or "").replace("\t", " ").strip(),
                "acc": "", "read": False,
            })
    log(f"{len(rows)} papers not yet in the repo or excluded")

    if not args.no_accession:
        # Pass 1: full text for every PMC record, not just open access (richest -
        # picks the data-availability accession).
        with_pmc = [r for r in rows if r["pmcid"]]
        for i, row in enumerate(with_pmc, 1):
            xml = full_text(row["pmcid"], row["oa"])
            row["read"], row["acc"] = bool(xml), accession_in(xml)
            if i % 100 == 0 or i == len(with_pmc):
                log(f"full text {i}/{len(with_pmc)} ({sum(r['acc'] != '' for r in with_pmc[:i])} with accession)")
        # Pass 2: text-mined annotations for everything still unresolved, INCLUDING
        # paywalled rows. Do not gate this on open access: author manuscripts and
        # other non-OA records have no fetchable full text but are still text-mined,
        # and that is the only way their accession ever surfaces.
        todo = [r["pmcid"] for r in rows if r["pmcid"] and not r["acc"]]
        mined: dict[str, str] = {}
        for i in range(0, len(todo), 8):
            mined.update(accessions_from_annotations(todo[i:i + 8]))
        log(f"annotations: {len(mined)}/{len(todo)} resolved")
        for row in rows:
            if not row["acc"]:
                row["acc"] = mined.get(row["pmcid"], "")
        # Pass 3: PubMed -> GEO links for whatever is left, including papers with
        # no PMCID at all (PubMed-only records, e.g. most Cell Press papers).
        todo = [r["pmid"] for r in rows if r["pmid"] and not r["acc"]]
        linked: dict[str, str] = {}
        for i in range(0, len(todo), 100):
            linked.update(geo_series_from_pubmed(todo[i:i + 100]))
        log(f"elink: {len(linked)}/{len(todo)} resolved")
        for row in rows:
            if not row["acc"]:
                row["acc"] = linked.get(row["pmid"], "")
        # Pass 4: a BioProject carrying the paper's own title (any repository).
        # Skipped when the full text was read and named no accession: that is
        # almost always a review or methods paper with no data of its own.
        todo = [r for r in rows if not r["acc"] and not r["read"]]
        for i, row in enumerate(todo, 1):
            row["acc"] = bioproject_by_title(row["title"], row["year"])
            if i % 100 == 0 or i == len(todo):
                log(f"title match {i}/{len(todo)} ({sum(r['acc'] != '' for r in todo[:i])} resolved)")

    for row in rows:
        print(f"{row['rng']}\t{row['doi']}\t{row['year']}\t"
              f"{'Y' if row['oa'] else 'N'}\t{row['pmcid']}\t{row['acc']}\t{row['title']}")
        if row["oa"]:
            accessible.append((row["doi"], row["acc"], row["title"]))
        elif row["acc"]:
            recovered.append((row["doi"], row["acc"], row["title"]))
        else:
            paywalled.append((row["doi"], row["year"], row["title"]))

    def block(label: str, rows: list) -> None:
        print(f"\n### {label} ({len(rows)})", file=sys.stderr)
        for row in rows:
            print("  " + " | ".join(str(x) for x in row), file=sys.stderr)

    block("ACCESSIBLE (open access — ready to expand into YAML)",
          [(d, a or "NO-ACCESSION-FOUND", t[:80]) for d, a, t in accessible])
    block("PAYWALLED but ACCESSION RECOVERED (curate from the repository record)",
          [(d, a, t[:80]) for d, a, t in recovered])
    block("PAYWALLED, no accession (flag for manual review)",
          [(d, y, t[:90]) for d, y, t in paywalled])
    if FAILED:
        log(f"\n### FAILED REQUESTS — accessions may be missing; rerun this range: {FAILED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
