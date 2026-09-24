---
name: rnacentral-probing-finder
description: >
  Find new RNA chemical-probing (SHAPE / DMS family) datasets in the literature
  and turn them into validated RNAcentral metadata YAMLs for this repo. Searches
  Europe PMC and GEO, triages hits (dedup vs repo, open access, own accession),
  expands accessions into runs, maps samples to the schema, and validates. Use for
  "find more chemical-probing datasets to add", "scan for new SHAPE/DMS papers",
  or the periodic dataset-refresh sweep.
metadata:
  author: Victoria Begley
  version: 1.0
---

# RNAcentral chemical-probing dataset finder

Grows `DMS/` and `SHAPE/`. Run from the repo root (`.venv/` present). Not for a
single known paper (curate it directly) or non-probing assays (RNA-seq, CLIP, MeRIP).

Scripts (`.claude/skills/rnacentral-probing-finder/scripts/`, no LLM):
- `find_probing_candidates.py` — Europe PMC search per year range → drop DOIs already
  in `DMS/`/`SHAPE/` or `excluded_dois.tsv` → open-access status + the study's
  accession (full text, else text-mined annotations). TSV on stdout, summary on stderr.
- `expand_accession.py <GSE|PRJNA|PRJEB|PRJDB> [--tsv]` — per run: accession, sample,
  sample and experiment titles, library name (DDBJ keeps the condition only there).

## 1. Find candidates

```bash
.venv/bin/python .claude/skills/rnacentral-probing-finder/scripts/find_probing_candidates.py \
    --ranges 2025-2026 > /tmp/candidates.tsv 2> /tmp/summary.txt
```

- **Always re-run the trailing 12 months.** Europe PMC keeps indexing behind you; the
  norovirus paper (00097/00098) was missed only because it was indexed after the
  sweep. The last sweep date heads `docs/open-leads.md`; update it after each sweep.
- **Also sweep GEO** — most probing datasets sit in papers whose abstract never
  names the assay:
  `esearch.fcgi?db=gds&term=<TERM>[All Fields]+AND+gse[Entry Type]&retmax=300`
  for `DMS-MaPseq`, `SHAPE-MaP`, `icSHAPE`, `Structure-seq`, `Structure-seq2`,
  `DMS-seq`, `DMS-MaP`, `SHAPE-seq`, `DMS probing`, `RNA structure probing`,
  `RNA structurome`, `NAI-N3`, `SHALiPE`, `keth-seq`, `PORE-cupine`, `CIRS-seq`,
  `DANCE-MaP`, `PAIR-MaP`, `LASER-seq`.
- **Paywalled papers still yield accessions.** Try, in order (they fail independently):
  1. Europe PMC annotations (the script does this):
     `annotations_api/annotationsByArticleIds?articleIds=PMC%3A<PMCID>&type=Accession%20Numbers&format=JSON`
     (≤8 ids per call; responses are unordered — key on `pmcid`).
  2. NCBI elink: `elink.fcgi?dbfrom=pubmed&db=gds&id=<PMID>` (lags publication).
  3. SRA/BioProject text search on title words or authors
     (`esearch.fcgi?db=sra&term=...`). Japanese groups often deposit at **DDBJ
     (`PRJDB…`)**, which GEO never links (tRNA structure-seq → PRJDB40244).
  With an accession, the GEO SOFT file alone is usually enough to curate (00097/00098).
- **`isOpenAccess: N` ≠ unreadable.** Author manuscripts (`authMan: Y`) have free
  full text; fetch as in step 3. Work newest PMCIDs first; old scans have no `<body>`.

## 2. Shortlist

Keep genuine probing studies that pass the scope gate. Drop targeted/single-RNA
studies (the commonest false positive — chemistry and replication look fine),
re-analyses whose accession is already in the repo, reviews, protocol chapters and
non-RNA "shape" hits.

## 3. Curate (one `general-purpose` subagent per paper)

Assign each candidate the next `rnastruct#####` up front (consecutive across both
folders) and give it `reference/curate-prompt.md`. Each subagent:

1. **Fetches full text to a file and greps it** — never reads the XML into context.
   Europe PMC first, NCBI as fallback (Europe PMC 500s on some records it holds;
   `curl -s` exits 0 on a 500, so test the content):
   ```bash
   curl -s "https://www.ebi.ac.uk/europepmc/webservices/rest/<PMCID>/fullTextXML" -o p.xml
   grep -q "<body" p.xml || curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=<PMCID>&retmode=xml" -o p.xml
   ```
   bioRxiv full text: `https://www.biorxiv.org/content/<DOI>v1.full-text` (browser UA).
2. **Confirms the accession is the study's own** (the #1 error), then **counts what
   the series holds** — SuperSeries and mixed probing/RNA-seq/Ribo-seq series are common:
   ```bash
   curl -s "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=<GSE>&targ=gsm&form=text&view=brief" \
     | grep '^!Sample_title' | sed -E 's/(rep[0-9]+|batch[0-9]+|D[0-9]+|[0-9]+h)//g' | sort | uniq -c
   ```
   Non-probing libraries go in the `# Excluded` block.
3. Runs `expand_accession.py`, applies the gate, and either returns
   `REJECT <id>: <reason>` (scope or not probing) or fills `docs/template.yaml` and
   validates, flagging any unreplicated arms for the user.

When a paywalled paper later becomes readable, re-check guessed fields — usually
`rna_type` ("poly(A)+ selected" → `mRNA`).

## 4. Consolidate

Renumber survivors so ids stay consecutive (file name + `dataset_id`), append every
reject to `excluded_dois.tsv` (doi, accession, gate, reason; viral constructs use
gate `scope-viral`) so it never resurfaces,
and run the full validation.

## Gate

(a) and (c) are hard rejects; (b) is a default the user overrides for special data.

- **(a)** genuine SHAPE- or DMS-family chemical probing that the schema can hold:
  read out by RT-stop or MaP (not nanopore) with a `chemical` already in
  `ChemicalEnum` — neither enum is being extended;
- **(b)** treated groups have **≥2 biological replicates** — a titration, time
  course, or pooled library (`rep123`) is n=1;
- **(c)** **transcriptome-wide**: the whole transcriptome, a whole viral genome (all
  segments), or a whole RNA class without gene selection (tRNA structurome).
  Undepleted total RNA analysed only for rRNA still counts (say mRNA coverage will
  be low, 00085). **Viral exception:** a sub-genomic region of a virus is in scope
  when it is native viral RNA — probed during infection, or wild-type viral sequence
  — since whole-genome viral data covers only one or two transcripts anyway.
  Designed truncations, mutant panels and synthetic constructs stay out.

**Reject for scope:** gene-specific RT/PCR primers or amplicons ("targeted",
"GSP", "amplicon" in the methods) — except native viral regions, above; one
lncRNA/mRNA/riboswitch/intron/construct or a chosen panel; in vitro transcripts of a
selected non-viral RNA; co-folded *combinations* of
genome segments (00077 dropped its `complex_B*` arm); cotranscriptional methods
(TECprobe, cotranscriptional SHAPE-Seq), which probe one nascent RNA by design; arms
whose condition label nothing defines (don't guess). Tell: run titles naming a non-viral gene (`COX1_P3`, `AR_V7`)
→ targeted; titles naming a condition (`minusAA_plusDMS_rep2`) → transcriptome-wide.

**Replicated treated groups with a single untreated are always kept** — the
pipeline reuses that control for every replicate (00005, 00017, 00074, 00076, 00086).

**Unreplicated data is kept when its conditions are special** — a cell-line panel
(00001, 00003), subcellular fractions (00043, 00044), developmental stages (00006),
a chaperone titration (00024) — and so are unreplicated arms or baselines beside
replicated ones (00004, 00057). Add a `# Kept as a special case: …` or
`# … kept deliberately` note. Ask the user before rejecting or dropping anything on
replication alone.

**Excluding an existing file:** keep it and set `comment: "failed QC: <reason>"`
(canonical: `no biological replicates`, `… for most conditions`).
`merge_metadata.py` skips only comments starting `failed QC`; any other comment is
processed.

## Field mapping

- **Folder**: `DMS/` for DMS; `SHAPE/` for NAI, NAI-N3, 1M7, 2A3, NMIA, 5NIA, ….
- **One strain and one method per file.** Split a series covering several strains
  (00072 + 00101–00104) or methods (icSHAPE 00096 / Frac-SHAPE 00107): lowest
  existing id for the first arm, new consecutive ids for the rest, siblings
  cross-referenced in the `#` block. The schema won't catch
  `strain: 17D, Asibi, Dakar` — grep `strain:.*,`.
- **condition**: no probe / DMSO / (−)reagent → `untreated`; probe → `treated`;
  heat/denaturant → `denatured` (add `denatured` to `context`). With three MaP arms
  (probe + DMSO + "unmodified"), "unmodified" is usually the denaturing control
  (Smola 2015); two untreated at one replicate means one is mislabelled (00072).
- **principle**: RT-stop (Structure-seq, icSHAPE) or `MaP`.
- **RT_enzyme**: TGIRT / MarathonRT / group II → `Group II intron`; SuperScript /
  Maxima / M-MLV → `M-MLV` ("M-MLV buffer" with TGIRT is still group II).
- **rna_type** (`null` fails): poly(A) → `mRNA`; total/rRNA-depleted → `total`;
  tRNA/<200 nt → `sRNA`; unsure → `total`.
- **obi** must match `chemical` (authority: `scripts/validate_obi_ids.py`): DMS
  `OBI:0001015`, NMIA `0001026`, 1M7 `0003885`, NAI `0003886`, NAI-N3 `0003887`, 2A3
  `0003888`, 1M6 `0003895`, 5NIA `0003896`; else `null`.
- **method**: a non-standard name gets an inline comment saying what it is
  (`method: CoSTseq  # DMS-MaP of nascent RNA …`).
- **publication.doi must resolve** (GEO-derived DOIs can be invented). For a
  preprint, check Crossref `relation.is-preprint-of` for a journal version.
- **Viral**: NCBI common name + top-level `strain:`. `scientific_name` rejects
  trailing digits — use the validating parent and note the exact taxid inline.
  GISAID-only isolates: bare `EPI_ISL_#######`, variant inline; prefer the paper's
  methods over GEO `data_processing` (often copied).
- **Viral genome lookup**: the pipeline keys `<scientific_name> (<strain>)`
  (lowercase, non-`[a-z0-9_]` → `_`) into nf-core-rnastructurome
  `conf/viral_genomes.config`; a miss falls back to a loose NCBI search that can
  return the wrong organism silently. If the key is missing, say in the `#` block
  that `--fasta` is needed (SARS-CoV-2, Dengue, HIV, Rotavirus all miss; Dengue
  also lacks from `VIRAL_ORGANISMS` in `merge_metadata.py`).
- **Optional fields** (`pH`, adapters, `umi_pattern`) stay `null` unless stated.
  The authors' analysis repo (fastp/cutadapt/umi_tools calls) is often the only
  source. Paired-end `adapter_3p` = `R1,R2`; `umi_pattern` = 5′ UMI of read 1
  (00090). `pH` is the probing buffer's, not the RT buffer's.
- `comment: null`.

## Naming

- `sample_group` = what is analysed together, minus the probe level; underscores,
  no whitespace. `sample_name` = `{sample_group}_{condition}_r{replicate}`, plus a
  distinguishing token only when runs share a replicate (see pairing). Rename
  both together.
- **First token = cell line or strain exactly as the repository states it**
  (HEK293 ≠ HEK293T; yeast `BY4741_WT`, `BY4741_dbp3KO`, never `Scer_`). Bacteria/
  archaea: full binomial or strain (`Bacillus_subtilis_37C`, `MG1655_delta_gcvB`),
  no `Ecoli`/`Bsub`.
- **Baseline group is the bare cell line** (`HeLa`, not `HeLa_Untreated`); suffix
  only the exceptions (`HeLa_NaAsO2`, `HeLa_invitro`, `HeLa_NaAsO2_Recover1h`).
  No tokens that are true of every sample: no in vivo suffix, no method
  (`icSHAPE_`), no `WholeCell`, no `rna_type`.
- **Viral**: spell the virus out, then strain (`Influenza_A_PR8`,
  `Bluetongue_virus_segment1`); drop `virus` when the strain identifies it
  (`Yellow_fever_Dakar`); no host cell or context token (`SARSCoV2_WT_NAI_treated_r1`).
- **Different perturbations are different groups** (±drug, WT/mutant, stress), each
  numbered from r1. **Probe-dose series: keep one dose** (the paper's) as r1–rN.
- Explain what a group *is* inline on its first `sample_group:` line
  (`sample_group: HeLa_NaAsO2  # sodium arsenite (500 uM, 1 h): …`).

## Control pairing (nf-core-rnastructurome)

Pairs treated/control on `sample_group` + `replicate`. A treated unit with no
control of its own falls back to the control group sharing the **longest leading
`_`-token prefix**: one at the same replicate → used; several → **fatal**; none at
that replicate but exactly one control in that arm → reused; else scored
treated-only (a different scoring method from its siblings — silent). A unit with
an untreated or denatured but no treated run is fatal. So:

- **One untreated in the arm → keep every treated replicate** (it is reused).
- **Two or more untreated but fewer than treated → drop treated replicates without
  a matching untreated** and list them (00040, 00089). Pair even if the authors
  never background-subtracted (00090/00091).
- **Mutant arms borrow the WT control** only via a shared first token
  (`BY4741_WT` ← `BY4741_dbp3KO`) and only at replicate numbers WT has (00091
  dropped knockout r3s). Different library types must **not** share it
  (`rRNA_BY4741_WT`).
- A single untreated or denatured control is fine; ≥2 applies to treated groups only.
- **Runs of one library may share `(group, condition, replicate)`** — tiling pools
  (00025/00030), segment pools (00024), a resequencing run (00035); the pipeline
  merges them. Name them apart (pool, `reseq`) and say so in the `#` block. Never
  merge *different* libraries this way (00014 folded targeted amplicons into its
  capture replicates).

## Where notes go

Between `landing_page:` and `run_accessions:` as `#` lines: which arm of a series
this is (with siblings), special-case or kept-deliberately notes, then
`# Excluded from this curation:` with one `# - <accessions> (<what>): <why>` per
omission. Keep it short; don't repeat wet-lab detail the schema fields already
hold, and don't cite the paper's sections. Never put notes in `comment:`.

## Validate — every file must pass

```bash
.venv/bin/linkml-validate -s schema/rnastruct.schema.yaml <file>
.venv/bin/python scripts/validate_obi_ids.py <file>
.venv/bin/python scripts/validate_ncbi_taxonomy.py <file>
.venv/bin/python scripts/check_metadata_uniqueness.py          # whole repo, once
.venv/bin/python - <file> <<'PY'                               # CI doesn't check this
import sys, yaml, collections as c
runs = yaml.safe_load(open(sys.argv[1]))["raw_data"]["run_accessions"]
if d := [k for k, n in c.Counter(r["sample_name"] for r in runs).items() if n > 1]:
    sys.exit(f"duplicate sample_name: {d}")
k = lambda r: (r["sample_group"], r["condition"], r["replicate"])
if s := [x for x, n in c.Counter(map(k, runs)).items() if n > 1]:
    print(f"shared (group, condition, replicate) — must be one library: {s}")
PY
```

The shell is zsh: list files literally in `for` loops (no word-splitting of `$VARS`).

## Notes

- Don't run git; the user commits.
- Relaunch a subagent that dies on a transient API error.
- Candidates not yet curated: `docs/open-leads.md`; move a row out when it is curated or rejected.
