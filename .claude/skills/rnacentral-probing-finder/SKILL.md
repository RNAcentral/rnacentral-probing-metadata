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

### 1b. ALSO sweep GEO directly — literature search alone misses most datasets

A no-date-limit rerun showed the literature query finds only a minority of
deposited probing datasets: many sit in papers whose **abstract never uses a
probing term** (the assay is one panel of a bigger study). Always run this
second, independent angle:

```bash
# per method/reagent term -> GEO series uids -> esummary for accession/taxon/pmid
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&term=DMS-MaPseq%5BAll+Fields%5D+AND+gse%5BEntry+Type%5D&retmax=300&retmode=json"
```

Terms that paid off: `DMS-MaPseq`, `SHAPE-MaP`, `icSHAPE`, `Structure-seq`,
`Structure-seq2`, `DMS-seq`, `DMS-MaP`, `SHAPE-seq`, `DMS probing`,
`RNA structure probing`, `RNA structurome`, `NAI-N3`, `SHALiPE`, `keth-seq`,
`PORE-cupine`, `CIRS-seq`, `DANCE-MaP`, `PAIR-MaP`, `LASER-seq`.

And for **paywalled** papers, recover the accession without journal access:

```bash
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&db=gds&id=<PMID>&retmode=json"
```

### 1c. Triage mechanically before reading anything

Resolve each candidate series to its SRA project, pull every run's sample and
experiment title, and count probing keywords. Series with ≥2 keyword-matching
run titles are worth a human look; the rest usually aren't. This turns hundreds
of candidates into a ranked list for free — see `docs/full-sweep-backlog.md` for
the worked run and `docs/full_sweep_triage.tsv` for the output format.

### 2. Shortlist by judgement

From the ACCESSIBLE hits, keep only genuine **transcriptome-wide** probing
studies (see the scope gate below); drop:
- **targeted / single-RNA studies** — one gene's amplicon, one lncRNA, a
  riboswitch construct, a pri-miRNA panel, in vitro transcripts of one RNA.
  These are the single most common false positive: the chemistry and the
  replication are both fine, so only the scope test catches them,
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

## The reject gate (all three must hold)

A candidate becomes a YAML **only if**:
- **(a)** it is genuine chemical probing (a SHAPE or DMS-family method), AND
- **(b)** every *treated* `sample_group` has **≥2 biological replicates**, AND
- **(c)** it is **transcriptome-wide** — the library covers the whole
  transcriptome (or the whole genome of a virus), not a selected RNA.

### (c) the scope gate — how to decide

**Keep:**
- rRNA-depleted or poly(A)-selected libraries probed and sequenced genome-wide
  (Structure-seq / Structure-seq2, DMS-seq, icSHAPE, DMS-MaPseq genome-wide mode).
- A **whole viral genome** — one RNA molecule, but it is that organism's entire
  transcriptome. All segments of a segmented virus counts.
- A whole RNA *class* sequenced without gene selection (e.g. the tRNA structurome).

**Reject:**
- Gene-specific RT or PCR primers → an amplicon. Look for "target-specific",
  "targeted DMS-MaPseq", "gene specific primer / GSP", "amplicon" in the methods.
- One lncRNA, one mRNA, one riboswitch, one intron, a designed construct, or a
  panel of a few chosen RNAs — however many replicates it has.
- In vitro transcripts of a selected RNA (unless it is the whole viral genome).

Fastest tell in practice: **the run/sample titles name a gene**
(`AR_V7`, `RORCWT`, `COX1_P3`, `PANDA`, `sfRNA1`) → targeted. Titles name a
condition or tissue (`Shoot_plusSalt_plusDMS_rep1`, `minusAA_plusDMS_rep2`) →
transcriptome-wide.

Common rejects: single modified sample + control (no replication); a concentration
or time *titration* (not biological replicates); a BioProject that is mostly plain
RNA-seq with one probing pair.

**Partially replicated designs**: if only one arm is replicated (e.g. drug-treated
n=2 but the no-drug control arm and the untreated control are n=1), do not keep
just the replicated arm when it is a perturbation rather than a baseline — fail the
dataset. Conversely, an unreplicated *extra* arm inside an otherwise replicated
design (a n=1 ± puromycin pair, a n=1 cell line) is simply dropped from
`run_accessions` with a note in `comment`.

**If a YAML already exists** (re-curation, or a file written before the gate was
applied), keep the file and mark it instead of deleting it, using the repo's
canonical wording so downstream tooling can filter on it:
`comment: "failed QC: no biological replicates"`,
`"failed QC: no biological replicates for most conditions"`, or
`"failed QC: no biological replicates for untreated"`. Any non-null `comment`
excludes the file from pipeline processing; `comment: null` means "run it".

## Field-mapping rules (the judgement step)

- **Folder**: `DMS/` if the chemical is DMS; `SHAPE/` for SHAPE reagents (NAI,
  NAI-N3, 1M7, 2A3, NMIA, 5NIA, …).
- **condition**: no probe / DMSO / (−)reagent → `untreated`; probe added →
  `treated`; heat/denaturant control → `denatured`.
- **sample_group**: the axis samples are analysed together on; everything except
  the probe level. **No whitespace — underscores.** See the naming rules below.
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

### Sample naming rules (lessons from the 00063–00096 re-curation)

- **In vivo is the default — never suffix it.** No `_invivo` / `_in_vivo` /
  `_vivo` on `sample_group`. The bare cell line / strain is the in-cell group
  (`HEK293T`, `K562`); only the exception gets a suffix (`K562_invitro`,
  `HEK293T_AsO2stress`, `HEK293T_DMplus`). Likewise don't encode `rna_type` in
  names (`HEK293_total_RNA` → `HEK293`); the field already records it.
- **Group name = cell line or strain exactly as the repository states it.** Read
  the GEO `characteristics` / `source_name` lines (`expand_accession.py` output):
  HEK293 vs HEK293**T** matters. For yeast use the strain (`BY4741`, `JWY6147`,
  `YOH001`) or `Scer_<genotype>` (`Scer_dbp3del`); never the bare species
  (`Scerevisiae`).
- **Bacteria / archaea: full binomial with underscores, or the strain.**
  `Bacillus_subtilis_37C`, `Escherichia_coli_WT`, `Methanosarcina_acetivorans_acetate`,
  or a named strain (`MG1655_delta_gcvB`, `E_coli_DH5a`). No ad-hoc abbreviations
  (`Bsub`, `Ecoli`, `Psav`, `Macetivorans`).
- **Different perturbations are different groups.** ±drug, ±demethylase, WT vs
  mutant, stress vs unstressed → separate `sample_group`s (`YOH001_pladB` /
  `YOH001_noPladB`), each with its own replicate numbering. Sharing one group and
  re-using replicate 1 for two perturbations is the classic silent error.
- **Probe-dose series: keep ONE dose.** Several concentrations of the same
  reagent are neither biological replicates nor separate groups (they'd need
  duplicated controls, and a run accession may appear only once in the repo).
  Pick the dose the paper analyses (usually the higher/standard one), list it as
  r1–rN, and drop the others. Don't renumber a second dose as r4–r6: the pipeline
  pairs controls by replicate number (see below), so r4–r6 would have no untreated
  and fail the all-or-none rf-normfactor check. Decode the tag first — GEO's
  `DMS0.02` is 2 % v/v DMS, not DMSO; check the methods.
- **Every treated replicate needs a control with the same replicate number.**
  nf-core/rnastructurome pairs on `sample_group` + `replicate` exactly; with
  `fuzzy_untreated_pairing` (default on) it falls back to (1) an untreated whose
  `sample_group` shares the text *before the first underscore* at the **same
  replicate**, then (2) the single untreated control if the whole file has exactly
  one. Anything else leaves that treated sample without a control and, because
  other groups have one, `rf-normfactor` errors (all-or-none). So: untreated
  r1–r3 for treated r1–r3; one lone untreated is fine only if it is the *only*
  untreated in the file.
- **`(sample_group, condition, replicate)` and `sample_name` must be unique within
  the file.** `check_metadata_uniqueness.py` does NOT check this (it only checks
  ids across files) — run the snippet in the validate step. The `_rN` suffix of
  `sample_name` should equal `replicate`.
- An untreated/no-probe control with a single replicate is fine; the ≥2 rule
  applies to *treated* groups only.

## Validate (the repo's CI checks) — every new file must pass all four

```bash
.venv/bin/linkml-validate -s schema/rnastruct.schema.yaml <file>
.venv/bin/python scripts/validate_obi_ids.py <file>
.venv/bin/python scripts/validate_ncbi_taxonomy.py <file>
.venv/bin/python scripts/check_metadata_uniqueness.py   # whole-repo, run once at the end
```

Plus the within-file check the CI scripts don't do:

```bash
.venv/bin/python - <file> <<'PY'
import sys, yaml, collections
runs = yaml.safe_load(open(sys.argv[1]))["raw_data"]["run_accessions"]
for key in (lambda r: r["sample_name"], lambda r: (r["sample_group"], r["condition"], r["replicate"])):
    dup = [k for k, n in collections.Counter(map(key, runs)).items() if n > 1]
    if dup: sys.exit(f"DUPLICATE within {sys.argv[1]}: {dup}")
print("within-file uniqueness OK")
PY
```

Note: this repo's shell is **zsh**, which does not word-split unquoted variables —
list files literally in `for` loops, don't pass a `$FILES` string.

## Notes

- Do NOT run git. Produce validated YAMLs and report; let the user commit.
- Paywalled candidates cannot be auto-curated — return their DOIs for manual review.
- Subagents occasionally die on a transient API error; just relaunch that one id.
- See `docs/finding-datasets-with-europepmc.md` and `docs/candidate-datasets.md`
  for the worked example this skill generalises.
