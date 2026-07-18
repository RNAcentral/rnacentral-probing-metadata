---
name: rnacentral-probing-finder

description: >
  Find new RNA chemical-probing (SHAPE / DMS family) datasets in the literature
  and turn them into validated RNAcentral metadata YAMLs for this repo. Searches
  Europe PMC per year range, triages hits (dedup vs repo, open-access, own
  accession), expands accessions into ENA runs, maps sample titles to the schema,
  and validates. Use for requests like "find more chemical-probing datasets to
  add", "scan for new SHAPE/DMS papers", or the periodic dataset-refresh sweep.

metadata:
  author: begley
  version: 1.0
---

# RNAcentral chemical-probing dataset finder

Repeatable workflow for growing `DMS/` and `SHAPE/` with new probing datasets.
Run it from the **repo root** (`.venv` and `scripts/` must be present). It builds
on the `europepmc-search` skill for discovery.

Two bundled scripts do the mechanical, LLM-free work:
- `.claude/skills/rnacentral-probing-finder/scripts/find_probing_candidates.py` — per-year Europe PMC search → dedup vs repo
  DOIs → resolve open-access + the study's own accession. Prints a TSV + an
  ACCESSIBLE / PAYWALLED summary.
- `.claude/skills/rnacentral-probing-finder/scripts/expand_accession.py` — `GSExxxxx` / `PRJNAxxxxx` → ENA run list
  (run accession + sample title).

## When to use

Any time you want to add fresh chemical-probing datasets: a periodic sweep, or
"find more like the ones we have". Not for single known papers (just curate those
directly) and not for non-probing assays (RNA-seq, CLIP, MeRIP).

## Procedure

### 1. Triage candidates (cheap — do first, no per-paper cost)

```bash
.venv/bin/python .claude/skills/rnacentral-probing-finder/scripts/find_probing_candidates.py \
    --ranges 2024-2025 2025-2026 > /tmp/candidates.tsv 2> /tmp/summary.txt
```

Pick year ranges newer than what the repo already has (check with
`for f in DMS/*.yaml SHAPE/*.yaml; do grep -m1 year: "$f"; done | grep -oE '[0-9]{4}' | sort | uniq -c`).
Read `/tmp/summary.txt` for the ACCESSIBLE list (open access, ready to curate) and
the PAYWALLED list (flag those DOIs for a human — you cannot read their full text).

### 2. Shortlist by judgement

From the ACCESSIBLE hits, keep genuine **transcriptome-wide or targeted probing
studies**; drop:
- re-analysis / method / tool papers whose accession is **already in the repo**
  (these grep-match a *re-used* accession — always a skip),
- pure image-processing "shape" false positives, protocol chapters, reviews.

### 3. Curate each shortlisted candidate (one subagent per paper)

Fan out — spawn one `general-purpose` subagent per candidate so the heavy
full-text reading stays out of the main context. Assign each a unique
`rnastruct#####` id up front (next consecutive across BOTH folders). Give each the
per-candidate prompt in `reference/curate-prompt.md`. Each subagent must:

1. Resolve PMCID + open-access, then `curl` the Europe PMC full-text XML to a temp
   file and **grep** it (never read the whole XML into context) for method,
   chemical, RT enzyme, pH, context, and the **data-availability** paragraph.
2. **Confirm the accession is the study's own**, not a cited/re-used one (the #1
   error). If it is re-used, find the real accession from the data-availability text.
3. `.claude/skills/rnacentral-probing-finder/scripts/expand_accession.py <acc>` for the run list.
4. Apply the **reject gate** (below). If it fails, write no file and report
   `REJECT <id>: <reason>`.
5. Otherwise fill `docs/template.yaml` and validate.

### 4. Consolidate

Collect subagent results. Renumber survivors so ids are consecutive with no gaps
left by rejects (rename file + update the `dataset_id:` line). Then run the full
validation suite (step 6 below) across all new files.

## The reject gate (both must hold)

A candidate becomes a YAML **only if**:
- **(a)** it is genuine chemical probing (a SHAPE or DMS-family method), AND
- **(b)** every *treated* `sample_group` has **≥2 biological replicates**.

Common rejects: single modified sample + control (no replication); a concentration
or time *titration* (not biological replicates); a BioProject that is mostly plain
RNA-seq with one probing pair.

## Field-mapping rules (the judgement step)

- **Folder**: `DMS/` if the chemical is DMS; `SHAPE/` for SHAPE reagents (NAI,
  NAI-N3, 1M7, 2A3, NMIA, 5NIA, …).
- **condition**: no probe / DMSO / (−)reagent → `untreated`; probe added →
  `treated`; heat/denaturant control → `denatured`.
- **sample_group**: the axis samples are analysed together on; everything except
  the probe level. **No whitespace — underscores.**
- **principle**: truncation / RT-stop method (Structure-seq, icSHAPE) → `RT-stop`;
  mutational profiling (MaP) → `MaP`.
- **RT_enzyme**: TGIRT / MarathonRT / group II → `Group II intron`;
  SuperScript / Maxima / M-MLV → `M-MLV`. Watch for "M-MLV **buffer**" used with a
  TGIRT enzyme — that's still `Group II intron`.
- **rna_type**: MUST be one of `mRNA` / `total` / `sRNA` — **`null` fails
  validation**. Poly(A)-selected → `mRNA`; rRNA-depleted/total → `total`;
  tRNA/<200 nt → `sRNA`; unsure → `total`.
- **obi** (must match `chemical`, enforced by `validate_obi_ids.py`):
  DMS→`OBI:0001015`, NMIA→`OBI:0001026`, 1M7→`OBI:0003885`, NAI→`OBI:0003886`,
  NAI-N3→`OBI:0003887`, 2A3→`OBI:0003888`, 1M6→`OBI:0003895`, 5NIA→`OBI:0003896`
  (see `scripts/validate_obi_ids.py` for the authoritative map; else `null`).
- **Viral datasets**: use the NCBI **common** name for `scientific_name` and add a
  top-level `strain:`. The schema's `scientific_name` pattern rejects trailing
  digits (e.g. "Human bocavirus 1" fails) — use the parent species name that
  validates and capture the sub-species in `strain:` with an inline note of the
  exact taxid.
- `comment: null`, and leave unknown optional fields (`pH`, adapters, `umi_pattern`)
  `null` unless the paper states them.

## Validate (the repo's CI checks) — every new file must pass all four

```bash
.venv/bin/linkml-validate -s schema/rnastruct.schema.yaml <file>
.venv/bin/python scripts/validate_obi_ids.py <file>
.venv/bin/python scripts/validate_ncbi_taxonomy.py <file>
.venv/bin/python scripts/check_metadata_uniqueness.py   # whole-repo, run once at the end
```

Note: this repo's shell is **zsh**, which does not word-split unquoted variables —
list files literally in `for` loops, don't pass a `$FILES` string.

## Notes

- Do NOT run git. Produce validated YAMLs and report; let the user commit.
- Paywalled candidates cannot be auto-curated — return their DOIs for manual review.
- Subagents occasionally die on a transient API error; just relaunch that one id.
- See `docs/finding-datasets-with-europepmc.md` and `docs/candidate-datasets.md`
  for the worked example this skill generalises.
