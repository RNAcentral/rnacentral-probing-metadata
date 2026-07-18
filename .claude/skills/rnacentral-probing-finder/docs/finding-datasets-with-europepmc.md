# Finding new chemical-probing datasets with Europe PMC

This document records how a candidate chemical-probing paper was found and turned
into a metadata YAML (`DMS/rnastruct00065.yaml`), and gives a copy-paste prompt so
the workflow can be repeated. It is deliberately **low-resource**: one literature
query, a handful of targeted API calls, no bulk downloads and no full-text scraping
of paywalled PDFs.

## The idea

Europe PMC indexes the biomedical literature and is queryable over a plain HTTP
GET (no key). We search it for recent papers describing transcriptome-wide chemical
probing (SHAPE / DMS variants), then for a promising hit we resolve the raw-data
accession from the open-access full text and expand it into per-run sample records
using the ENA / GEO APIs. Finally we fill in `docs/template.yaml` and validate.

The whole flow uses three public, unauthenticated APIs:

| Step | API | Why |
|------|-----|-----|
| Find papers | Europe PMC REST (`europepmc-search` skill) | keyword search over titles/abstracts |
| Get data accession | Europe PMC full-text XML (`.../PMC…/fullTextXML`) | open-access "Data availability" section |
| Expand to runs | ENA Portal `filereport` / NCBI GEO `acc.cgi` | run accessions, sample titles, replicates |

## Selection criteria (applied in order)

A candidate is only worth turning into a YAML if **all** of these hold:

1. **Method is chemical probing** — SHAPE-MaP, icSHAPE, DMS-MaPseq, Structure-seq, NAI-MaP, etc.
2. **More recent than what the repo already has** — most existing entries are ≤2022, so prefer 2024–2025. Check with:
   `for f in DMS/*.yaml SHAPE/*.yaml; do grep -m1 year: "$f"; done | grep -oE '[0-9]{4}' | sort | uniq -c`
3. **Not already in the repo** — its DOI must not appear in `grep -rh doi: DMS SHAPE`.
4. **Raw reads are deposited** — a GEO/SRA/ENA accession in the "Data availability" section.
5. **Biological replicates exist** — each treated `sample_group` needs ≥2 reps (repo requirement). Confirm from the ENA sample titles.
6. **Open access** — so the full text can be read via Europe PMC without a paywall (`isOpenAccess: Y`).

## The steps that were run

### 1. Search Europe PMC (one query)

```bash
cd ~/.claude/skills/europepmc-search
python scripts/europepmc_search.py \
  'ABSTRACT:"DMS-MaPseq" OR ABSTRACT:"SHAPE-MaP" OR ABSTRACT:"icSHAPE" OR ABSTRACT:"Structure-seq" OR ABSTRACT:"transcriptome-wide RNA structure"' \
  --from 2024 --to 2025
```

This returned ~50 hits. Triaging the titles for genuine transcriptome-wide probing
(not single-transcript studies) surfaced the 2025 human tRNA structurome paper
*"In vivo structure profiling reveals human cytosolic and mitochondrial tRNA
structurome…"* (`10.1038/s41467-025-59435-5`, Nat Commun).

### 2. Resolve the paper's PMC id and open-access status

```bash
curl -s 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:"10.1038/s41467-025-59435-5"&format=json&resultType=lite' \
  | python -c "import sys,json;r=json.load(sys.stdin)['resultList']['result'][0];print(r.get('pmcid'),r.get('isOpenAccess'))"
# -> PMC12125218 Y
```

### 3. Pull the "Data availability" section from the open full text

```bash
curl -s 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12125218/fullTextXML' \
  | grep -oE 'GSE[0-9]{4,}|PRJNA[0-9]{4,}|SRP[0-9]{4,}'
```

The Data availability text names **GSE262888** as the data *generated for this study*
(GSE198441 is a re-used dataset, so it is ignored).

### 4. Expand the accession into per-run sample records

```bash
# GEO series -> BioProject
curl -s 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE262888&targ=self&form=text&view=full' \
  | grep -i BioProject          # -> PRJNA1094587

# BioProject -> runs + sample titles (this is where replicates/conditions come from)
curl -s 'https://www.ebi.ac.uk/ena/portal/api/filereport?accession=PRJNA1094587&result=read_run&fields=run_accession,experiment_title,sample_title&format=tsv'
```

The 42 sample titles follow the pattern `{context} DMS{conc} {DMplus|DMminus} rep{n}`:
- `DMS0` = no probe → `condition: untreated`; `DMS0.02` / `DMS0.05` = probe → `condition: treated`.
- `DMplus`/`DMminus` = ± AlkB demethylase → used as the `sample_group` axis so samples analysed together share everything except the DMS level.
- `rep1..3` → three biological replicates per group ✔ (criterion 5 satisfied).

### 5. Fill the template and map schema fields

| Schema field | Value | Source |
|---|---|---|
| `experiment.method` | `DMS-MaPseq` | paper method |
| `experiment.principle` | `MaP` (mutational profiling) | paper method |
| `experiment.RT_enzyme` | `M-MLV` | RT is Maxima H Minus / SuperScript (M-MLV-derived) |
| `experiment.chemical` / `obi` | `DMS` / `OBI:0001015` | DMS probe |
| `experiment.rna_type` | `sRNA` | tRNA (<200 nt) |
| `experiment.context` | `[in_vivo, in_vitro]` | in vivo, arsenite-stress and in vitro samples |
| `organism` | `Homo sapiens` / `9606` | HEK293 cells |

### 6. Validate exactly as CI does

```bash
.venv/bin/linkml-validate -s schema/rnastruct.schema.yaml DMS/rnastruct00065.yaml   # -> No issues found
.venv/bin/python scripts/check_metadata_uniqueness.py                               # -> passed
```

## Reusable prompt

Paste this into Claude Code (in this repo) to repeat the process for a fresh dataset:

> Using the `europepmc-search` skill, find **one** recent (2024–2025) chemical-probing
> paper I can add to this repo, using as few resources as possible. Requirements:
> 1. The paper must use a chemical-probing method (SHAPE-MaP, icSHAPE, DMS-MaPseq, Structure-seq, NAI-MaP, etc.), be transcriptome-wide, and be **newer** than the papers already in `DMS/` and `SHAPE/`.
> 2. Its DOI must **not** already appear in `grep -rh doi: DMS SHAPE`.
> 3. It must deposit raw reads (GEO/SRA/ENA) **with biological replicates** (each treated group ≥2 reps — see the README rule).
> 4. It must be open access so you can read the "Data availability" section via the Europe PMC full-text XML endpoint (`.../PMC<id>/fullTextXML`) rather than a paywalled publisher page.
>
> Workflow: run a single Europe PMC query and triage the titles; for the best hit,
> resolve its PMCID + open-access flag, grep the full-text XML for the study's own
> GEO/SRA accession, then use the ENA `filereport` API (and GEO `acc.cgi` to get the
> BioProject if needed) to list run accessions with sample titles. Map DMS-untreated
> samples to `condition: untreated` and probed samples to `treated`, pick a
> `sample_group` axis so grouped samples differ only by probe level, and set
> `replicate` from the sample titles. Fill in a copy of `docs/template.yaml` with the
> next consecutive `rnastruct#####` id (check both `DMS/` and `SHAPE/`), then validate
> with `.venv/bin/linkml-validate -s schema/rnastruct.schema.yaml <file>` and
> `.venv/bin/python scripts/check_metadata_uniqueness.py`. Show me the resulting YAML.

## Batch mode (scaling to many datasets)

The single-paper flow above is scripted into two reusable, LLM-free tools so a whole
year range can be triaged for a few tokens:

- **`.claude/skills/rnacentral-probing-finder/scripts/find_probing_candidates.py`** — searches Europe PMC per year range,
  drops DOIs already in the repo, and for each remaining hit resolves open-access
  status + PMCID and (for open-access hits) the study's own accession. Prints a TSV
  plus an `ACCESSIBLE` / `PAYWALLED` summary on stderr.

  ```bash
  .venv/bin/python .claude/skills/rnacentral-probing-finder/scripts/find_probing_candidates.py \
      --ranges 2022-2023 2023-2024 2024-2025 2025-2026 > candidates.tsv
  ```

- **`.claude/skills/rnacentral-probing-finder/scripts/expand_accession.py`** — turns a `GSExxxxx` / `PRJNAxxxxx` into the ENA
  run list (run + sample title) that becomes `raw_data.run_accessions`.

  ```bash
  .venv/bin/python .claude/skills/rnacentral-probing-finder/scripts/expand_accession.py GSE237160
  ```

The result of one such run is written up in
[`candidate-datasets.md`](candidate-datasets.md): the created YAMLs, an
open-access "review next" queue, and a paywalled list flagged for manual review.

**Why not fully automate the YAML writing?** The mechanical steps (search, dedup,
open-access check, accession + run resolution) are safe to script. The remaining
judgement — is the study genuinely transcriptome-wide, which runs are the probing
subset, how do sample titles map to `condition`/`sample_group`/`replicate`, is the
grep-matched accession the study's own or a re-used one — is where errors creep in,
so those are left for a human (or a per-candidate reasoning pass) to confirm.

## Notes & caveats

- **Always verify the accession belongs to the study**, not a re-used dataset cited in the same section (both appear in the XML). The paper text distinguishes them ("generated for this study" vs "downloaded from").
- The `europepmc-search` script needs the full query in the URL; a fetch tool that drops the query string returns only the default 25-hit page.
- Publisher pages (Nature, Springer) redirect to auth — use the Europe PMC full-text XML for open-access articles instead of the publisher HTML.
- This finds candidates and populates metadata; a human should still sanity-check the biology (e.g. whether a "targeted-capture" study is really transcriptome-wide) before opening a PR.
