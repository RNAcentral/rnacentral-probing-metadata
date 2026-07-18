# Candidate chemical-probing datasets (batch triage)

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

## YAMLs created this session (24 datasets, 00065–00088)

All pass linkml-validate + OBI + NCBI-taxonomy + uniqueness. Repo went 63 → 87.
Produced across three passes: an initial narrow-query batch (00065–00074, incl. two
datasets recovered from existing papers), then two broadened-query subagent batches
(00075–00088).

| YAML | DOI | Accession | Dataset |
|------|-----|-----------|---------|
| `DMS/rnastruct00065` | 10.1038/s41467-025-59435-5 | GSE262888 | Human tRNA structurome, DMS-MaPseq (HEK293) |
| `SHAPE/rnastruct00066` | 10.1038/s41467-024-54000-y | GSE237160 | DHX36 structurome — human HEK293T, NAI Structure-seq |
| `SHAPE/rnastruct00067` | 10.1038/s41467-024-54000-y | GSE237160 | DHX36 structurome — mouse C2C12, NAI Structure-seq |
| `SHAPE/rnastruct00068` | 10.1093/nar/gkae494 | PRJNA1072546 | Yeast Ty3 retrotransposon, SHAPE-MaP/NAI |
| `SHAPE/rnastruct00069` | 10.3389/fcell.2021.766532 | PRJNA625172 | *P. falciparum* structurome, icSHAPE/NAI-N3 |
| `DMS/rnastruct00070` | 10.1038/s41467-025-56149-6 | GSE245536 | Telomerase hTR, DMS-MaPseq (human, TGIRT) |
| `SHAPE/rnastruct00071` | 10.1261/rna.080488.125 | GSE243328 | lncRNA SChLAP1, SHAPE-MaP/5NIA (human) |
| `DMS/rnastruct00072` | 10.1073/pnas.2320782121 | PRJNA955716 | Bocavirus BocaSR, DMS-MaPseq |
| `DMS/rnastruct00073` | 10.1038/s41587-025-02739-0 | GSE247244 | Human HEK293 total RNA, DMS-MaPseq (from 00064's paper) |
| `DMS/rnastruct00074` | 10.1038/s41467-026-70801-9 | GSE302505 | Phage T4 *td* intron, DMS-MaPseq (restored from removed 00063) |
| `DMS/rnastruct00075` | 10.1038/s41594-025-01565-x | GSE209857 | *S. cerevisiae* intron structurome, DMS-MaPseq |
| `DMS/rnastruct00076` | 10.1038/s41467-026-69648-x | PRJNA938111 | *B. subtilis* glycine riboswitch, DMS (TECprobe-VL) |
| `DMS/rnastruct00077` | 10.1261/rna.079652.123 | GSE224126 | *B. subtilis* RNA thermometers, DMS Structure-seq2 ⚠️ |
| `DMS/rnastruct00078` | 10.1261/rna.079687.123 | GSE229536 | *M. acetivorans* (Archaea), DMS Structure-seq2 |
| `SHAPE/rnastruct00079` | 10.1038/s41467-025-63297-2 | GSE279203 | SARS-CoV-2 (5 variants), SHAPE-MaP/NAI |
| `SHAPE/rnastruct00080` | 10.1038/s41467-025-60425-w | PRJNA992462 | *E. coli* SRP hairpin, SHAPE/BzCN (split from 00084) |
| `SHAPE/rnastruct00081` | 10.1038/s41467-025-60425-w | PRJNA992462 | *C. beijerinckii* pfl ZTP riboswitch, SHAPE/BzCN (split) |
| `SHAPE/rnastruct00082` | 10.1038/s41467-025-60425-w | PRJNA992462 | *B. cereus* crcB fluoride riboswitch, SHAPE/BzCN (split) |
| `SHAPE/rnastruct00083` | 10.1093/nar/gkaf820 | GSE272797 | TDP-43 study, human SHALiPE-seq/NAI (accession corrected from RBNS subseries) |
| `DMS/rnastruct00084` | 10.1093/nar/gkaf477 | PRJNA1197522 | *E. coli* Mn-sensing riboswitch, DMS-MaPseq |
| `SHAPE/rnastruct00085` | 10.1261/rna.079926.123 | GSE274121 | *L. monocytogenes* SreA riboswitch, SHAPE-MaP/1M7 |
| `SHAPE/rnastruct00086` | 10.1093/nar/gkad056 | PRJNA906919 | *C. antarcticum* preQ1-II riboswitch, ReCo-icSHAPE/NAI |
| `SHAPE/rnastruct00087` | 10.1038/s41467-023-43395-9 | PRJNA929456 | *C. beijerinckii* ZTP riboswitch, TECprobe/BzCN |
| `SHAPE/rnastruct00088` | 10.1093/nar/gkac102 | PRJNA776034 | *B. subtilis* yxjA riboswitch, SHAPE-Seq/BzCN |

⚠️ `00077`: GEO per-sample metadata is corrupt — the ±DMS treated/untreated direction
and temperature labels were reconstructed from filenames; verify before pipeline use.

Two datasets from an already-in-repo paper's BioProject that were **too large to split
cleanly** are left uncurated: the 1M7/SHAPE and TECprobe-DMS arms of PRJNA1197522, and
the DMS arm of the coordinated-folding TECprobe project — each would need its own id.

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

## Open-access candidates worth reviewing next (not yet made)

All open access with the study's own accession; ranked by fit. A human should
confirm the probing subset and replicate structure before writing the YAML.

| Priority | DOI | Accession | Note |
|---|---|---|---|
| High | 10.1038/s41592-024-02335-1 | GSE266070 | Human transcriptome structural switches (Nat Methods 2024). 144 runs mixing SHAPE/DMS with functional-screen DNA/RNA bins — **identify the probing-only runs first**. |
| Med | 10.1093/nar/gkae494 | PRJNA1072546 | Yeast Ty3 retrotransposon RNA genome structure (2024). |
| Med | 10.1093/nar/gkae185 | GSE223117 | Conserved intronic secondary structures / branch sites (2024). |
| Med | 10.3389/fcell.2021.766532 | PRJNA625172 | Plasmodium falciparum structurome, thermoregulation (2021 — older than repo top but transcriptome-wide). |
| Low (viral, single genome) | 10.1128/jvi.00635-23 | PRJNA936272 | SARS-CoV-2 SL-II probing (2023). |
| Low (viral) | 10.1093/nar/gkae404 | PRJEB71404 | Bluetongue virus genome RNA network (2024). |
| Low (viral) | 10.1038/s44319-025-00598-z | PRJNA1219967 | Adenovirus genome packaging (2025). |
| Low (viral) | 10.1038/s41564-025-02047-y | PRJNA1153987 | Yellow fever 17D attenuation (2025). |
| Low (viral) | 10.7554/elife.103923 | GSE271098 | Viral RNA druggable regions (2025). |
| Low (lncRNA, targeted) | 10.1261/rna.080488.125 | GSE243328 | lncRNA SChLAP1 structure (2025). |
| Low (lncRNA, targeted) | 10.1016/j.jbc.2025.110172 | GSE279192 | lncRNA DRAIC hairpin (2025). |
| Low (targeted) | 10.1038/s41467-025-56149-6 | GSE245536 | Telomerase RNA heterogeneity, DMS-MaPseq (2025). |
| Low (targeted) | 10.1093/nar/gkae220 | PRJNA1048882 | Androgen receptor FL/V7 transcripts (2024). |
| Low (targeted) | 10.15252/embr.202256021 | PRJNA855586 | SRSF3 / miR-17-92 cluster (2023). |
| Low (plant) | 10.3390/plants14050780 | PRJNA1175151 | DNA-damage-induced RNA structure changes, plant (2025). |
| Review | 10.1073/pnas.2320782121 | PRJNA955716 | m6A on parvovirus sncRNA (2024). |
| Review | 10.1021/acscentsci.2c00149 | PRJNA767082 | RNA–small molecule structure probing (2022). |
| Borderline | 10.1186/s13059-024-03186-x | PRJNA1049869 | Plant 3'UTR DMS-MaPseq — **targeted-capture of specific constructs**, not truly transcriptome-wide. |

**Skip — re-analysis / method papers whose accession is already in the repo:**
`10.1038/s41467-022-31875-3` (GSE117840, dStruct), `10.1186/s12859-024-05704-x`
(GSE145805, AStruct), `10.1093/bib/bbag301` (GSE131506, VIRSE).

## Paywalled — flag for manual review

Europe PMC could not read the full text (`isOpenAccess: N`), so the accession
could not be auto-resolved. These need a human with journal access.

### Likely genuine new probing datasets (highest value to check)

| DOI | Year | Title |
|---|---|---|
| 10.1016/j.molcel.2024.02.005 | 2024 | Structural atlas of human primary microRNAs generated by SHAPE-MaP |
| 10.1016/j.celrep.2024.114544 | 2024 | Hfq mediates transcriptome-wide RNA structurome reprogramming under virulence |
| 10.1021/acschembio.4c00538 | 2024 | Disulfide Tethering to Map Small Molecule Binding Sites Transcriptome-wide |
| 10.1261/rna.081029.126 | 2026 | Optimized tRNA structure-seq reveals robust tRNA secondary structures in *S. cerevisiae* |
| 10.1261/rna.080976.126 | 2026 | Cancer-associated synonymous mutations reveal stress-dependent mRNA folding |
| 10.1016/j.cell.2025.12.030 | 2026 | Mechanistic insights into RNA chaperoning by Ro60 and La autoantigens |
| 10.1016/j.jbc.2026.113194 | 2026 | SARS-CoV-2 5'-UTR stem-loops activate OAS1 (viral) |
| 10.1128/jvi.00898-26 | 2026 | Comparative analysis of flavivirus sfRNA dynamics and secondary structure (viral) |
| 10.1016/j.jmb.2023.168417 | 2024 | Telomerase RNA structure in *Physcomitrium patens* (targeted) |
| 10.1002/cpz1.70038 | 2024 | DMS-MapSeq analysis of ASO binding to lncRNA PANDA (targeted) |
| 10.1016/j.ymeth.2022.05.001 | 2022 | DMS-MaPseq of DEAD-box proteins in ribosome assembly |

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
