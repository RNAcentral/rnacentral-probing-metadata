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
  ACCESSIBLE / PAYWALLED summary. Accessions come from the open-access full text
  where there is one, and otherwise from Europe PMC's text-mined annotations, so
  paywalled hits still surface an accession.
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

**Always re-run the trailing 12 months, even if a sweep "already covered" them.**
Europe PMC indexes continuously, so a range is never finished — it keeps filling in
behind you. The Cell 2026 norovirus paper (rnastruct00097/00098) was missed for
exactly this reason and nothing else: the sweep ran 2026-07-19, the paper was first
indexed 2026-08-22. Both the literature query and the GEO sweep below match it
perfectly — it simply did not exist yet. Check `git log -1 --format=%ad` on
`docs/sweep_*.tsv` to see when the last sweep ran, and re-sweep from a few months
before that date. Adding query terms would not have helped; re-running would.

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

And for **paywalled** papers, recover the accession without journal access. Try both
— they fail independently:

```bash
# (1) Europe PMC text-mined accessions. Works on author manuscripts and other non-OA
#     records whose fullTextXML 500s or is withheld. Up to 8 ids per call; the
#     response is NOT in request order, so key on each record's own "pmcid" field.
curl -s "https://www.ebi.ac.uk/europepmc/annotations_api/annotationsByArticleIds?articleIds=PMC%3A<PMCID>&type=Accession%20Numbers&format=JSON"

# (2) NCBI elink. Only works once GEO has been linked to the PMID, which lags.
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&db=gds&id=<PMID>&retmode=json"
```

`find_probing_candidates.py` already applies (1) automatically to every hit it could
not resolve from full text, and reports those under **PAYWALLED but ACCESSION
RECOVERED**. Worked example: the Cell 2026 norovirus paper is `isOpenAccess: N`,
its `fullTextXML` returns HTTP 500, and elink returned nothing — (1) returned
`GSE310315` on the first call. Re-running (1) over the 336 already-swept rows that
had a PMCID but no accession recovered 14, all of them paywalled rows the old code
never even attempted; among them the Ro60/La series in `pending/` and
`GSE285333` (10.1016/j.molcel.2026.03.029), which is still uncurated.

### 1c. Triage mechanically before reading anything

Resolve each candidate series to its SRA project, pull every run's sample and
experiment title, and count probing keywords. Series with ≥2 keyword-matching
run titles are worth a human look; the rest usually aren't. This turns hundreds
of candidates into a ranked list for free — see `docs/full-sweep-backlog.md` for
the worked run and `docs/full_sweep_triage.tsv` for the output format.

### 1d. Re-check the PAYWALLED pile — `isOpenAccess: N` does not mean unreadable

Europe PMC's OA flag is about the **licence**, not availability. Author manuscripts
(`authMan: Y`) sit at `isOpenAccess: N` yet are free to read, and the triage drops
them before anything is ever fetched. That pile is worth a second pass; use the
normal step-3 fetch, which falls back to NCBI when Europe PMC errors:

```bash
# every triage row that has a PMCID but was not called open access
awk -F'\t' 'NR>1 && $5!="" && $4!="Y"{print $5}' docs/full_sweep_papers.tsv |
while read -r p; do
  curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=$p&retmode=xml" -o "$p.xml"
  [ "$(grep -c '<body' "$p.xml")" -gt 0 ] && echo "RECOVERED $p"
  sleep 0.4
done
```

Scale as of Sept 2026: `docs/full_sweep_papers.tsv` holds **544** rows that are
`oa=N` *with* a PMCID. A 12-row sample recovered **3** with a real `<body>`, so
expect roughly a quarter of the pile to be curatable. rnastruct00092 is the worked
case: filed as "Paywalled paper" with guessed fields, but PMC8074864 (`inEPMC: Y`,
`authMan: Y`, `isOpenAccess: N`) yields ~187 kB of full text. Misses cluster on
**old PMCIDs** (roughly `PMC1######` and below — pre-XML scans with no `<body>`),
so work the pile newest-first.

**The two archives hold the same records** — a 15-PMCID spread from `PMC53364` to
`PMC12679999` was 15/15 present in Europe PMC, all `inEPMC: Y`, and 24/24 recent
PMC `SHAPE-MaP` hits likewise. So there is no need to search both. The only reason
to keep NCBI in the loop is **delivery**: Europe PMC's `fullTextXML` returns
`HTTP 500` for some records it does index, and NCBI serves those fine.

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

1. Resolve PMCID + open-access, then `curl` the full text to a temp file and
   **grep** it (never read the whole XML into context) for method, chemical, RT
   enzyme, pH, context, and the **data-availability** paragraph.

   **Europe PMC first, NCBI PMC as the backup.** Both archives index the same
   records (see 1d), so there is nothing to gain from searching both — but Europe
   PMC's `fullTextXML` answers `HTTP 500` for some records it does hold, and NCBI
   serves those. `curl -s` exits 0 on a 500 and writes the JSON error body to your
   file, so **never trust the exit code — test the content**:
   ```bash
   curl -s "https://www.ebi.ac.uk/europepmc/webservices/rest/<PMCID>/fullTextXML" -o paper.xml
   grep -q "<body" paper.xml ||
     curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=<PMCID>&retmode=xml" -o paper.xml
   grep -c "<body" paper.xml   # 1 = real full text; 0 = neither archive served it
   ```
   Worked case: 10.1016/j.molcel.2020.11.014 (rnastruct00092) was curated as
   "Paywalled paper" with guessed fields; Europe PMC 500s on it while efetch on
   PMC8074864 returns ~187 kB. A PMC link a user pastes is the same thing — take
   the `PMC#######` out of it and use efetch, rather than fetching the article
   page as HTML.

   **When a paper only becomes readable later**, re-check the fields the original
   curation guessed and drop the caveat from the file. `rna_type` is the one that
   is usually wrong: "poly(A)+ selected" in the methods means `mRNA`, not `total`
   (rnastruct00089 was `total` until its methods turned up).
2. **Confirm the accession is the study's own**, not a cited/re-used one (the #1
   error). If it is re-used, find the real accession from the data-availability text.
   **Then check what is actually in the series.** A GEO accession is often a
   SuperSeries, or mixes probing with RNA-seq / ribosome profiling / decay
   libraries, so count the sample types before assuming the series is all probing:
   ```bash
   curl -s "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=<GSE>&targ=gsm&form=text&view=brief" \
     | grep '^!Sample_title' | sed -E 's/(rep[0-9]+|batch[0-9]+|D[0-9]+|[0-9]+h)//g' | sort | uniq -c
   ```
   GSE275594 is a SuperSeries whose probing arm is 12 of its samples; GSE156671 is
   95 samples of which 31 are icSHAPE. Put the non-probing libraries in the
   `# Excluded from this curation:` block so the count is auditable.
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
- Undepleted total RNA that the paper only analyses for rRNA (e.g. an RT/reagent
  benchmark on 16S/23S). It is still an unselected library; keep it and say in a
  YAML comment that mRNA coverage will be low (decision on rnastruct00085).

**Reject:**
- Gene-specific RT or PCR primers → an amplicon. Look for "target-specific",
  "targeted DMS-MaPseq", "gene specific primer / GSP", "amplicon" in the methods.
- One lncRNA, one mRNA, one riboswitch, one intron, a designed construct, or a
  panel of a few chosen RNAs — however many replicates it has.
- In vitro transcripts of a selected RNA (unless it is the whole viral genome).
- **Subsets of a segmented genome.** The ten segments each probed on their own are
  the whole genome and are kept; arbitrary *combinations* of some segments
  (co-folded complexes, assembly intermediates) are selected subsets and are not.
  Drop the combination arm and keep the single-segment arm (rnastruct00077 lost 13
  `complex_B*` groups, 57 runs, this way).
- **Conditions whose label nothing defines.** If neither the repository nor the
  paper says what a group's condition *is* — an opaque `B7`, an unexplained code —
  the reactivities would reach RNAcentral under a condition no reader can
  interpret. Exclude the arm and say in the block that the composition is
  undocumented. Do not guess it from the paper's narrative.

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
`run_accessions` and listed in the `# Excluded from this curation:` block (see
"Where curation notes go" below) — never in `comment`, which would take the
whole file out of the pipeline.

**If a YAML already exists** (re-curation, or a file written before the gate was
applied), keep the file and mark it instead of deleting it, using the repo's
canonical wording so downstream tooling can filter on it:
`comment: "failed QC: no biological replicates"`,
`"failed QC: no biological replicates for most conditions"`, or
`"failed QC: no biological replicates for untreated"`.

**Only a `failed QC` comment excludes a file.** `scripts/merge_metadata.py` tests
`dataset_comment.startswith("failed QC")` and skips those; every other comment,
however long, is processed normally (rnastruct00092 / 00094 / 00096 all carry prose
comments and still run). So the reason to keep curation notes out of `comment:` is
the repo convention below, **not** a pipeline switch — do not claim otherwise in a
YAML or a commit message.

## Field-mapping rules (the judgement step)

- **Folder**: `DMS/` if the chemical is DMS; `SHAPE/` for SHAPE reagents (NAI,
  NAI-N3, 1M7, 2A3, NMIA, 5NIA, …).
- **condition**: no probe / DMSO / (−)reagent → `untreated`; probe added →
  `treated`; heat/denaturant control → `denatured`.
  **Three arms means read the protocol, not the titles.** A MaP series with
  NAI + DMSO + "unmodified" is not two untreated arms: DMSO is the vehicle control
  (`untreated`) and the "unmodified"/"no-reagent" portion is usually the
  **denaturing control** the library prep needs (Smola et al. 2015), so it is
  `denatured` and `denatured` joins `context`. Two untreated at the same replicate
  number is the tell that one of them is mislabelled (rnastruct00072 and its
  00101–00104 siblings were curated this way first).
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
  exact taxid. In `sample_group` / `sample_name` **spell the virus out** with
  underscores, then the strain: `SARS-CoV-2_USA-WA1`, `Bluetongue_virus_segment1`,
  `Porcine_epidemic_diarrhea_virus_AJ1102` — not an abbreviation (`MNV_CW3`,
  `ZIKV_`, `IAV_`, `PEDV_`, `BTV_`; older files still have these). Drop a
  redundant `virus` token when the strain already identifies the isolate
  (`Yellow_fever_Dakar`, not `Yellow_fever_virus_Dakar`).
  **No host cell and no context token in the name** — `VeroE6_`, `Huh7_`,
  `_incell` are already carried by schema fields, so `SARSCoV2_WT_NAI_treated_r1`,
  not `VeroE6_SARSCoV2_WT_incell_NAI_treated_r1` (user decision, Sept 2026;
  `Murine_norovirus_CW3_BV2` predates it). Rename `sample_name` and `sample_group`
  together — a mismatch between the two is a defect.
- **One strain per file.** `organism.strain` names the single reference the whole
  file is probed against, so a series covering several strains becomes several
  files, not one file with a comma-separated `strain:`. Nothing in the schema
  catches this — `strain: 17D (vaccine), Asibi, Dakar` validated cleanly — so grep
  for it: `grep -n "strain:.*," SHAPE/*.yaml DMS/*.yaml`. Keep the lowest existing
  id for the first arm, allocate new consecutive ids for the rest, and cross-
  reference the siblings in the `#` block (GSE279203 → 00072 + 00101–00104;
  GSE275594 → 00075 + 00105–00106).
- **Strain for a GISAID-only isolate**: record the bare `EPI_ISL_#######` with the
  variant name in an inline comment. Many SARS-CoV-2 variants were never deposited
  in GenBank — check before assuming a GenBank accession exists, and prefer the
  paper's methods over GEO's `data_processing`, which is often copied from an
  earlier submission (rnastruct00072: methods say EPI_ISL_574502, GEO says
  EPI_ISL_407987).
- **Check the pipeline can actually resolve the viral genome.** `merge_metadata.py`
  emits the organism as `<scientific_name> (<strain>)`, which nf-core/rnastructurome
  normalises to a key (lowercase, non-`[a-z0-9_]` → `_`) and looks up in
  `conf/viral_genomes.config`. On a miss it tries Ensembl, then falls back to a
  loose NCBI keyword search that returns whatever matches — for
  `SARS-CoV-2 (EPI_ISL_574502)` that is *Theobroma cacao* snoRNAs, silently. After
  curating a viral dataset, derive the key and confirm it is in that map; if it is
  not, say so in the `#` block so whoever runs it knows to pass `--fasta`. As of
  Sept 2026 ~20 viral files miss, including every SARS-CoV-2, Dengue, HIV and
  Rotavirus entry (Dengue misses because `merge_metadata.py`'s `VIRAL_ORGANISMS`
  set omits it, so its strain never reaches the organism string at all).
- `comment: null`, and leave unknown optional fields (`pH`, adapters, `umi_pattern`)
  `null` unless the paper states them. The **authors' analysis repo** (GitHub /
  Zenodo link in the key-resources table) is often the only place adapters and
  UMIs are spelled out: look for the fastp / cutadapt / umi_tools call. For
  paired-end libraries `adapter_3p` is the R1,R2 read-through pair, comma-separated
  (`AAGATCGGAAGAGCACACGTCTGAACTCCAGTCAC,AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT`);
  `umi_pattern` is the UMI at the 5′ end of read 1. Derive them from the
  oligo table (5′ adapter → R1 side, template-switching / RT primer → R2 side)
  and check against the pipeline's `--adapter_sequence` values (rnastruct00090).
  `pH` is the pH of the probing buffer the reagent is added in (Bicine pH 8.0 →
  `8.0`), not the RT buffer.
- **Non-standard `method` names get an inline YAML comment** on the same line
  explaining what the assay is — e.g. `method: CoSTseq  # DMS-MaP of nascent RNA
  (biotin-CTP run-on + streptavidin pulldown)` — so nobody has to open the paper
  to learn it is a DMS-MaP variant.

### Sample naming rules (lessons from the 00063–00096 re-curation)

- **In vivo is the default — never suffix it.** No `_invivo` / `_in_vivo` /
  `_vivo` on `sample_group`. The bare cell line / strain is the in-cell group
  (`HEK293T`, `K562`); only the exception gets a suffix (`K562_invitro`,
  `HEK293T_AsO2stress`, `HEK293T_DMplus`). Likewise don't encode `rna_type` in
  names (`HEK293_total_RNA` → `HEK293`); the field already records it.
- **Group name = cell line or strain exactly as the repository states it.** Read
  the GEO `characteristics` / `source_name` lines (`expand_accession.py` output):
  HEK293 vs HEK293**T** matters. For yeast use the strain (`BY4741`, `JWY6147`,
  `YOH001`) and put the genotype after it: `BY4741_WT`, `BY4741_dbp3KO`,
  `YKW100_galactose`. Never the bare species (`Scerevisiae`) and not
  `Scer_<genotype>` — the strain must be the **first token** so mutant arms
  can borrow the wild-type untreated (see pairing below).
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
  and be scored on a different method from r1–r3. Decode the tag first — GEO's
  `DMS0.02` is 2 % v/v DMS, not DMSO; check the methods.
- **Every treated replicate needs a control with the same replicate number.**
  nf-core/rnastructurome (`normalise_reactivities` + `selectClosestControl`)
  pairs on `sample_group` + `replicate` exactly. With `fuzzy_untreated_pairing`
  (default on) a treated group with no untreated of its own falls back to the
  untreated whose `sample_group` shares the **longest run of leading `_`-tokens**
  (at least one), preferring the **same replicate**; if none is at the same
  replicate and the closest arm holds **exactly one** control, that one is reused
  across replicates; otherwise the treated sample gets **no control** and is
  scored treated-only (Zubradt) while its siblings are scored against untreated
  (Siegfried) — a silent within-group inconsistency, not an error.
  Consequences for curation:
  - **More treated than untreated — count the untreated first.**
    - **Exactly one untreated in the arm → keep every treated replicate.**
      `selectClosestControl` reuses that single control across replicates (the
      "exactly one control" branch above), so the group is scored consistently
      and nothing needs dropping. Do **not** drop the surplus and do **not** fail
      the file: rnastruct00005 / 00014 / 00017 / 00074 / 00076 / 00086 are all
      active on this layout.
    - **Two or more untreated, still fewer than treated → drop the surplus
      treated** (those with no untreated at the same number) and list them in the
      exclusion block. Here the fallback has several candidates at other
      replicates, cannot choose, and leaves the extra treated scored treated-only
      while its siblings are scored against untreated (rnastruct00040).
    Do this even when the authors never used the untreated for background
    subtraction (CoSTseq only shows it as a no-DMS negative control): we pair
    because we have the samples; it is our curation choice, say so in the block
    (rnastruct00090 / 00091).
  - **Mutant / perturbation arms with no untreated of their own** borrow the
    wild-type one, so name them to share the leading token with the WT group
    (`BY4741_WT` ← `BY4741_dbp3KO`; `HFF_uninfected` ← `HFF_infected_HCMV_72hr`)
    and check a WT untreated exists at **every replicate number the mutant
    uses** — if WT has untreated r1–r2 only, the mutants' r3 must go too
    (rnastruct00091 lost r3 of five knockouts this way).
  - **Different library types must NOT share the leading token.** Mature-rRNA
    libraries (fragmented total RNA) next to oligo-dT mRNA libraries of the same
    strain get a distinct prefix (`rRNA_BY4741_WT`) so they do not borrow the
    mRNA untreated; with no untreated at all they are scored treated-only,
    consistently within the group, which is fine.
  - One lone untreated is fine only if it is the *only* untreated in its arm.
- **Where curation notes go.** `comment:` is a pipeline switch: any non-null
  value takes the file **out of processing**, so it holds only the canonical
  `failed QC: …` strings. Everything else — omitted libraries and why, kept-but-
  unusual groups, which arm of a series this file is — goes in a YAML comment
  block between `landing_page:` and `run_accessions:`, headed
  `# Excluded from this curation:` with one `# - <accessions> (<what>): <why>`
  bullet per omission (rnastruct00026, 00057, 00088, 00090, 00091 are the
  models). **What a group *is*** — the cell line, the perturbation, an unusual
  library type — goes as an inline `# …` on the `sample_group:` line of the
  group's **first** sample (`sample_group: MCF7_hippuristanol # MCF7 treated
  with hippuristanol, an eIF4A1 inhibitor`; rnastruct00076/00081/00082/00091),
  not as a comment block above the sample. Wet-lab detail that is already
  captured by schema fields (buffer, RT enzyme, adapters) does not need
  repeating anywhere.
- **`(sample_group, condition, replicate)` and `sample_name` must be unique within
  the file.** `check_metadata_uniqueness.py` does NOT check this (it only checks
  ids across files) — run the snippet in the validate step. The `_rN` suffix of
  `sample_name` should equal `replicate`.
- An untreated/no-probe **or denatured** control with a single replicate is
  fine; the ≥2 rule applies to *treated* groups only. A lone denatured is the
  one case the fuzzy fallback handles cleanly (single control in the closest
  arm → shared by every replicate and every prefix-matching group), so keep it
  (rnastruct00099 GSM8700908) — it does mean prefix-matching arms are all
  normalised against that one denatured reference.

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
- Paywalled candidates cannot be auto-curated from full text — but if an accession was
  recovered, the GEO/SRA record alone usually carries enough (design, reagent, buffer,
  replicates) to curate. rnastruct00097/00098 were built entirely from the GEO SOFT
  file (`ftp.ncbi.nlm.nih.gov/geo/series/GSE310nnn/<acc>/soft/<acc>_family.soft.gz`)
  with no access to the paper. Return DOIs for manual review only when there is no
  accession either.
- Subagents occasionally die on a transient API error; just relaunch that one id.
- See `docs/finding-datasets-with-europepmc.md` and `docs/candidate-datasets.md`
  for the worked example this skill generalises.
