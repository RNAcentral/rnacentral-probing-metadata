# Candidate chemical-probing datasets (batch triage)

> **Superseded in part by [`full-sweep-backlog.md`](full-sweep-backlog.md).** The
> sweeps recorded below were capped at 2022+ and driven only by abstract terms. A
> later no-date-limit rerun, combined with a GEO-side sweep, found ~120 further
> genuine probing series the repo was missing — most of them pre-2022. Read that
> file first; this one remains the record of the 2022-2026 passes.

Generated with `.claude/skills/rnacentral-probing-finder/scripts/find_probing_candidates.py` over Europe PMC, per year range
(2022-2023, 2023-2024, 2024-2025, 2025-2026). The initial narrow method-term query
returned 72 new papers (48 open-access, 24 paywalled). The query was later **broadened**
for max recall (generic "chemical probing" + reagent/method terms, scoped by
`ABSTRACT:"RNA"`): the broadened sweep returned **620 new candidates** (368 open-access),
saved to `sweep_2022-2026_broad.tsv` and `sweep_new_accessible_leads.tsv` in this folder.
Higher recall traded for more noise (re-analyses, non-chemical methods) — filtered by the
per-paper reject gate.

- Raw triage table: regenerate with `.venv/bin/python .claude/skills/rnacentral-probing-finder/scripts/find_probing_candidates.py > candidates.tsv`
- Expansion of any accession into ENA runs: `.venv/bin/python .claude/skills/rnacentral-probing-finder/scripts/expand_accession.py <GSE|PRJNA>`

## YAMLs created this session (24 made, 10 kept as 00065-00074)

Originally 00065-00088. **A later scope decision removed every targeted /
single-RNA dataset** (the reject gate now requires transcriptome-wide scope - see
SKILL.md), so 14 of the 24 were deleted and the survivors renumbered.

### Kept (transcriptome-wide)

| YAML | DOI | Accession | Dataset | was |
|------|-----|-----------|---------|-----|
| `DMS/rnastruct00065` | 10.1038/s41467-025-59435-5 | GSE262888 | Human tRNA structurome, DMS-MaPseq (HEK293) | 00065 |
| `SHAPE/rnastruct00066` | 10.1038/s41467-024-54000-y | GSE237160 | DHX36 structurome - human HEK293T, NAI Structure-seq | 00066 |
| `SHAPE/rnastruct00067` | 10.1038/s41467-024-54000-y | GSE237160 | DHX36 structurome - mouse C2C12, NAI Structure-seq | 00067 |
| `SHAPE/rnastruct00068` | 10.3389/fcell.2021.766532 | PRJNA625172 | *P. falciparum* structurome, icSHAPE/NAI-N3 | 00069 |
| `DMS/rnastruct00069` | 10.1038/s41587-025-02739-0 | GSE247244 | Human HEK293 total RNA, DMS-MaPseq | 00073 |
| `DMS/rnastruct00070` | 10.1038/s41594-025-01565-x | GSE209857 | *S. cerevisiae* intron structurome, DMS-MaPseq | 00075 |
| `DMS/rnastruct00071` | 10.1261/rna.079652.123 | GSE224126 | *B. subtilis* RNA thermometers, DMS Structure-seq2 | 00077 |
| `DMS/rnastruct00072` | 10.1261/rna.079687.123 | GSE229536 | *M. acetivorans* (Archaea), DMS Structure-seq2 | 00078 |
| `SHAPE/rnastruct00073` | 10.1038/s41467-025-63297-2 | GSE279203 | SARS-CoV-2 (5 variants), SHAPE-MaP/NAI - whole viral genome | 00079 |
| `SHAPE/rnastruct00074` | 10.1093/nar/gkaf820 | GSE272797 | TDP-43 study, human SHALiPE-seq/NAI | 00083 |

⚠️ `00071` (was 00077): GEO per-sample metadata is corrupt - the ±DMS
treated/untreated direction and temperature labels were reconstructed from
filenames; verify before pipeline use.

Two judgement calls kept as transcriptome-wide: `00065` (tRNA structurome - a
whole RNA class, no gene selection) and `00070` (genome-wide DMS-MaPseq that is
merely *analysed* for introns).

### Removed as targeted (were 00068-00088)

| was | Accession | What was probed |
|---|---|---|
| 00068 | PRJNA1072546 | Ty3 retrotransposon gRNA |
| 00070 | GSE245536 | telomerase hTR |
| 00071 | GSE243328 | lncRNA SChLAP1 |
| 00072 | PRJNA955716 | bocavirus BocaSR (a single ~140 nt sncRNA, not the genome) |
| 00074 | GSE302505 | phage T4 *td* intron |
| 00076 | PRJNA938111 | *B. subtilis* glycine riboswitch (TECprobe-VL) |
| 00080 | PRJNA992462 | *E. coli* SRP hairpin (TECprobe-LM) |
| 00081 | PRJNA992462 | *C. beijerinckii* pfl ZTP riboswitch |
| 00082 | PRJNA992462 | *B. cereus* crcB fluoride riboswitch |
| 00084 | PRJNA1197522 | *E. coli* alx Mn-sensing riboswitch |
| 00085 | GSE274121 | *L. monocytogenes* SreA riboswitch |
| 00086 | PRJNA906919 | *C. antarcticum* preQ1-II riboswitch |
| 00087 | PRJNA929456 | *C. beijerinckii* ZTP riboswitch |
| 00088 | PRJNA776034 | *B. subtilis* yxjA riboswitch |

**TECprobe / cotranscriptional-folding methods are inherently single-RNA** - the
technique probes one nascent transcript, so no TECprobe dataset can ever pass the
scope gate. Same for SHAPE-Seq cotranscriptional variants. Don't re-curate these.

This also retires the note about the "too large to split cleanly" arms of
PRJNA1197522 and the coordinated-folding TECprobe project: both are targeted, so
they are out of scope, not pending.


### Rejected (verified, not curated)

| DOI / Accession | Reason |
|-----------------|--------|
| GSE223117 · PRJNA936272 | no biological replicates (single modified samples) |
| PRJNA1153987 (yellow fever) | API-failed, then not re-pursued |
| GSE61508 (HIV HiCapR) | proximity-ligation, not SHAPE/DMS; re-used accession |
| PRJNA1392914 (BIVID-MaP) | ligand-binding footprinting, synthetic constructs |
| GSE200706 · PRJNA1182414 · PRJNA1077397 · PRJNA767082 | genuine probing but no biological replicates (single/titration/technical SAMN) |
| PRJNA714002 (Candida) | nextPARS — enzymatic probing, not chemical |
| PRJNA1071355 | rG4-seq (RT-stalling), not reagent probing |
| GSE127188 · PRJNA762705 · GSE301761 | re-used accession / RNA-seq, not this study's own probing data |
| PRJNA946372 (single-cell) | technical replicates only (shared SAMN) |
| PRJEB60419 | **empty ENA project** — no runs deposited |
| PRJNA929486 (avian IBV) | 2 runs = 2 isolates, no replicates |
| PRJNA1375461 · GSE266263 · GSE262014 | no chemical-probing data deposited |

### Flagged for a human
- **PRJEB44384** — *P. falciparum* in-vivo DMS+NAI structurome (distinct from 00069);
  genuine and open but the ENA project has **no retrievable reads** (embargo/suppression?).
  Re-attempt once reads are released.

## YAMLs created in the follow-up pass (9 kept, renumbered to 00075-00083)

Worked the "open-access candidates worth reviewing next" backlog below to
exhaustion, plus the paywalled candidates whose accession could be recovered via
PubMed->GEO/BioProject elinks. **A later scope decision removed every targeted /
single-RNA dataset** (see the scope gate in SKILL.md), so the ids below are the
survivors after renumbering. Repo now holds **82** datasets.

| YAML | DOI | Accession | Dataset |
|------|-----|-----------|---------|
| `SHAPE/rnastruct00075` | 10.7554/elife.103923 | GSE271098 | PEDV genome (strain AJ1102), SHAPE-MaP/NAI in Vero E6 |
| `SHAPE/rnastruct00076` | 10.1038/s41564-025-02047-y | **GSE275594** | Yellow fever 17D/Asibi/Dakar, SHAPE-MaP/2A3 (accession corrected - PRJNA1153987 is plain viral genome sequencing) |
| `DMS/rnastruct00077` | 10.3390/plants14050780 | PRJNA1175151 | *A. thaliana* +/- MMS DNA damage, DMS-MaPseq |
| `SHAPE/rnastruct00078` | 10.1093/nar/gkae404 | PRJEB71404 | Bluetongue virus (BTV-1) all 10 segments + complexes, SHAPE-MaP/1M7 (102 runs) |
| `DMS/rnastruct00079` | 10.1016/j.celrep.2024.114544 | GSE216157 | *P. savastanoi* Hfq structurome, DMS-seq (paywalled) |

...plus `00080`-`00083` from the full-history sweep, listed in
[`full-sweep-backlog.md`](full-sweep-backlog.md).

### Removed as targeted (curated, validated, then deleted on the scope rule)

PRJNA1048882 (androgen receptor amplicons) - PRJNA855586 (miR-17-92 amplicons) -
GSE266070 (RORC 3'UTR amplicon) - PRJNA1049869 (3'-end target-specific, LUC
transgene constructs) - GSE254361 (pri-miRNA panel) - GSE261913 (COX1 amplicons) -
GSE250290 (lncRNA PANDA) - GSE270001 (Powassan 3'UTR/sfRNA constructs, both the
DMS and 1M7 arms) - GSE83821 (yeast pre-rRNA from purified particles).

All were genuine, well-replicated probing data; they fail only the scope gate. The
run tables are reconstructible from the accessions above if the policy changes.

### Rejected in this pass

| DOI / Accession | Reason |
|-----------------|--------|
| 10.1038/s44319-025-00598-z - PRJNA1219967 | DMS-seq of adenoviral **DNA** (nucleoprotein core maturation) - not RNA probing |
| 10.1016/j.jbc.2025.110172 - GSE279192 | lncRNA DRAIC: one 5NIA run and one DMSO run, no replicates (also targeted) |
| 10.1016/j.cell.2025.12.030 - GSE290478 | Ro60/La paper's linked GEO series holds only 2 RIP-Seq runs, no probing data |

Schema change: `Porcine epidemic diarrhea virus` added to the
`organism.scientific_name` pattern alternation (4-word viral name that the
binomial/trinomial branch cannot match).

## Paywalled stubs filed in `pending/`

Seven paywalled candidates could not be resolved to an accession even via
PubMed→GEO/BioProject elinks. Stub YAMLs with everything derivable pre-filled and
the rest marked `TODO` live in `pending/` (outside `DMS/`/`SHAPE/` so CI stays
green): tRNA structure-seq yeast, synonymous-mutation mRNA folding, Ro60/La,
SARS-CoV-2 5'UTR/OAS1, flavivirus sfRNA, *Physcomitrium* telomerase RNA, and the
DEAD-box ribosome-assembly Methods chapter. See `pending/README.md`.

## Open-access candidates worth reviewing next (WORKED — all resolved above)

All open access with the study's own accession; ranked by fit. Status column
added after the follow-up pass.

| Priority | DOI | Accession | Note | Status |
|---|---|---|---|---|
| High | 10.1038/s41592-024-02335-1 | GSE266070 | Human transcriptome structural switches (Nat Methods 2024). 144 runs mixing SHAPE/DMS with functional-screen DNA/RNA bins — **identify the probing-only runs first**. | removed (targeted) |
| Med | 10.1093/nar/gkae494 | PRJNA1072546 | Yeast Ty3 retrotransposon RNA genome structure (2024). | removed (targeted) |
| Med | 10.1093/nar/gkae185 | GSE223117 | Conserved intronic secondary structures / branch sites (2024). | rejected (no bio reps) |
| Med | 10.3389/fcell.2021.766532 | PRJNA625172 | Plasmodium falciparum structurome, thermoregulation (2021 — older than repo top but transcriptome-wide). | → 00068 |
| Low (viral, single genome) | 10.1128/jvi.00635-23 | PRJNA936272 | SARS-CoV-2 SL-II probing (2023). | rejected (no bio reps) |
| Low (viral) | 10.1093/nar/gkae404 | PRJEB71404 | Bluetongue virus genome RNA network (2024). | → 00078 |
| Low (viral) | 10.1038/s44319-025-00598-z | PRJNA1219967 | Adenovirus genome packaging (2025). | rejected (DNA probing) |
| Low (viral) | 10.1038/s41564-025-02047-y | PRJNA1153987 | Yellow fever 17D attenuation (2025). | → 00076 (via GSE275594) |
| Low (viral) | 10.7554/elife.103923 | GSE271098 | Viral RNA druggable regions (2025). | → 00075 |
| Low (lncRNA, targeted) | 10.1261/rna.080488.125 | GSE243328 | lncRNA SChLAP1 structure (2025). | removed (targeted) |
| Low (lncRNA, targeted) | 10.1016/j.jbc.2025.110172 | GSE279192 | lncRNA DRAIC hairpin (2025). | rejected (no bio reps) |
| Low (targeted) | 10.1038/s41467-025-56149-6 | GSE245536 | Telomerase RNA heterogeneity, DMS-MaPseq (2025). | removed (targeted) |
| Low (targeted) | 10.1093/nar/gkae220 | PRJNA1048882 | Androgen receptor FL/V7 transcripts (2024). | removed (targeted) |
| Low (targeted) | 10.15252/embr.202256021 | PRJNA855586 | SRSF3 / miR-17-92 cluster (2023). | removed (targeted) |
| Low (plant) | 10.3390/plants14050780 | PRJNA1175151 | DNA-damage-induced RNA structure changes, plant (2025). | → 00077 |
| Review | 10.1073/pnas.2320782121 | PRJNA955716 | m6A on parvovirus sncRNA (2024). | removed (targeted) |
| Review | 10.1021/acscentsci.2c00149 | PRJNA767082 | RNA–small molecule structure probing (2022). | rejected (no bio reps) |
| Borderline | 10.1186/s13059-024-03186-x | PRJNA1049869 | Plant 3'UTR DMS-MaPseq — **targeted-capture of specific constructs**, not truly transcriptome-wide. | removed (targeted) |

**Skip — re-analysis / method papers whose accession is already in the repo:**
`10.1038/s41467-022-31875-3` (GSE117840, dStruct), `10.1186/s12859-024-05704-x`
(GSE145805, AStruct), `10.1093/bib/bbag301` (GSE131506, VIRSE).

## Paywalled — flag for manual review

Europe PMC could not read the full text (`isOpenAccess: N`), so the accession
could not be auto-resolved. These need a human with journal access.

### Likely genuine new probing datasets (highest value to check)

Trick that worked for half of these without journal access: PubMed → NCBI
`elink` into `gds` / `bioproject` recovers the deposited accession even when the
full text is unreadable, and the GEO sample titles are usually enough to build
the run table.

```bash
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&db=gds&id=<PMID>&retmode=json"
```

| DOI | Year | Title | Status |
|---|---|---|---|
| 10.1016/j.molcel.2024.02.005 | 2024 | Structural atlas of human primary microRNAs generated by SHAPE-MaP | GSE254361 → removed (targeted: pri-miRNA panel) |
| 10.1016/j.celrep.2024.114544 | 2024 | Hfq mediates transcriptome-wide RNA structurome reprogramming under virulence | GSE216157 → 00079 |
| 10.1021/acschembio.4c00538 | 2024 | Disulfide Tethering to Map Small Molecule Binding Sites Transcriptome-wide | GSE261913 → removed (targeted: COX1 amplicons) |
| 10.1002/cpz1.70038 | 2024 | DMS-MapSeq analysis of ASO binding to lncRNA PANDA (targeted) | GSE250290 → removed (targeted: lncRNA PANDA) |
| 10.1016/j.cell.2025.12.030 | 2026 | Mechanistic insights into RNA chaperoning by Ro60 and La autoantigens | GSE290478 = RIP-Seq only → stub |
| 10.1261/rna.081029.126 | 2026 | Optimized tRNA structure-seq reveals robust tRNA secondary structures in *S. cerevisiae* | no elink → stub |
| 10.1261/rna.080976.126 | 2026 | Cancer-associated synonymous mutations reveal stress-dependent mRNA folding | no elink → stub |
| 10.1016/j.jbc.2026.113194 | 2026 | SARS-CoV-2 5'-UTR stem-loops activate OAS1 (viral) | no elink → stub |
| 10.1128/jvi.00898-26 | 2026 | Comparative analysis of flavivirus sfRNA dynamics and secondary structure (viral) | no elink → stub |
| 10.1016/j.jmb.2023.168417 | 2024 | Telomerase RNA structure in *Physcomitrium patens* (targeted) | no elink → stub |
| 10.1016/j.ymeth.2022.05.001 | 2022 | DMS-MaPseq of DEAD-box proteins in ribosome assembly | no elink → stub |

### Not datasets — protocols, methods, modeling, or off-topic false positives (ignore)

`10.1007/978-1-0716-1851-6_16`, `10.1007/978-1-0716-3191-1_6`,
`10.1007/978-1-0716-3519-3_4`, `10.1007/978-1-0716-4079-1_12` (protocol chapters);
`10.3791/64820`, `10.3791/69945` (JoVE protocols);
`10.1016/bs.mie.2023.03.021`, `10.1016/bs.mie.2023.05.006`,
`10.1016/bs.mie.2023.05.008` (Methods in Enzymology chapters);
`10.1093/nar/gkae289` (generative modeling, no probing data);
`10.1021/acschembio.5c00548` (SHAPE probe development);
`10.1109/cvprw67362.2025.00642`, `10.1109/tmi.2025.3642381`
(image-processing "shape" papers — keyword false positives).
