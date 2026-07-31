# Full-history sweep backlog (no date limit)

Produced by rerunning the finder over **all years (1990-2026)** plus an
independent GEO-side sweep. The earlier passes were capped at 2022+ and driven
only by abstract terms, so everything below was invisible to them.

## What the sweep did

1. **Literature, no date limit** - `find_probing_candidates.py` query terms run
   over 1990-2026 in year chunks: **2,205 unique papers**, 2,152 after dropping
   DOIs already in the repo. Raw list: `full_sweep_papers.tsv`.
2. **PubMed -> NCBI elink** (`db=gds|bioproject|sra`) for every one of those
   PMIDs: only **117** have a deposited dataset linked from PubMed. This step
   works for paywalled papers too, which is how four paywalled datasets were
   recovered.
3. **GEO-side sweep** (the step that found most of the misses) - `esearch` over
   `db=gds` for 31 method/reagent terms: **206 series**, 151 not in the repo.
   Literature search alone misses these because many probing datasets sit in
   papers whose abstract never uses a probing term.
4. **Merge + dedupe** vs repo accessions, repo DOIs and the documented reject
   list -> **236 candidate series** (`full_sweep_master_candidates.tsv`).
5. **Mechanical triage** - resolve each series to its SRA project, pull every
   run's sample/experiment title, and score probing keywords:
   **122 STRONG / 3 WEAK / 111 NONE** (`full_sweep_triage.tsv`).

**Headline:** 122 series carried a strong probing signal and were absent from the
repo. After the transcriptome-wide scope gate was added (reject-gate condition
(c)), **26 were judged in scope**; working them dropped 4 more on closer reading
(2 were actually targeted, 2 fail the replicate gate) and parked 3 nanopore
series pending a `principle` enum decision, leaving **19 curated as 14 YAMLs**.
Most of both groups are pre-2022, which the old 2022+ date cap could never see.

## Curated from this sweep so far

| YAML | Accession | Dataset |
|------|-----------|---------|
| `DMS/rnastruct00080` | GSE124866 | *A. thaliana* shoot/root +/- salt, Structure-seq2 (24 runs) |
| `DMS/rnastruct00081` | GSE100714 | Rice 22 C vs 42 C heat structurome, Structure-seq2 |
| `DMS/rnastruct00082` | GSE148936 | *B. subtilis* +/- amino acids, Structure-seq2 |
| `DMS/rnastruct00083` | GSE134865 | MCF7 +/- hippuristanol (eIF4A), Structure-seq2 |
| `DMS/rnastruct00084` | GSE233607 | *E. coli* in vivo, Structure-seq2 (DMS arm; EDC arm has no schema chemical) |
| `DMS/rnastruct00085` | GSE210478 | EBV-infected BJAB-B1 transcriptome, Structure-seq2 |
| `DMS/rnastruct00086` | GSE254895 | *E. coli* in vivo DMS-MaP (DMS control arm of the ETC-reagent paper) |
| `DMS/rnastruct00087` | GSE102069 | HFF across an HCMV infection timecourse, DMS-seq |
| `DMS/rnastruct00088` | GSE246523 | Human mitochondrial mRNA structurome, mitoDMS-MaPseq |
| `DMS/rnastruct00089` | GSE236224 | Neuronal differentiation, DMS arm (hESC + NPC) |
| `SHAPE/rnastruct00090` | GSE156671 | Neuronal differentiation, icSHAPE arm (D0/D7/D8/D14, 2 batches) |
| `DMS/rnastruct00091` | GSE254264 | Yeast CoSTseq arm (nascent RNA base-pairing) |
| `DMS/rnastruct00092` | GSE254264 | Yeast DMS-MaPseq arm (mature-RNA comparator) |
| `SHAPE/rnastruct00093` | GSE149767 | fSHAPE in K562 / HepG2 / HeLa, in-cell + deproteinised |
| `SHAPE/rnastruct00094` | GSE143120 + GSE143096 | ENCODE icSHAPE, K562 (NAI-N3 series + its DMSO series) |
| `SHAPE/rnastruct00095` | GSE143121 + GSE142946 | ENCODE icSHAPE, HepG2 |
| `SHAPE/rnastruct00096` | GSE143102 + GSE142891 | ENCODE icSHAPE, GM12878 |
| `SHAPE/rnastruct00097` | GSE288910 | HeLa arsenite stress + recovery, icSHAPE / FracSHAPE (80 samples, 18 groups) |

Two more were curated and then **deleted on the scope rule** (targeted, not
transcriptome-wide): GSE270001 (Powassan 3'UTR/sfRNA constructs, DMS and 1M7 arms)
and GSE83821 (yeast pre-rRNA from affinity-purified particles).

**Scope gate applies to this whole backlog** - see SKILL.md. The re-triage below
applies it row by row.

## Rejected from this sweep

| Accession | Reason |
|---|---|
| GSE244468 | **reclassified targeted** - the DMS-MaPseq arm probes only the HIV-1 ribosomal frameshift site |
| GSE285333 | **reclassified targeted** - every sample is a named RNA (16S/23S rRNA, U1/U2 snRNA, tmRNA, 7SK, RNase P, p4-p6) |
| GSE149018 | tNet-MaPseq WT arm has a single replicate; the tNet-PIPseq arm is enzymatic (RNase V1/ONE) |
| GSE103421 | DMS-seq timepoints are n=1 each; only in-vitro pair is replicated and has no control; DMS-MaPseq arm is targeted (cspA) |
| GSE304702 / GSE304703 / GSE309111 / GSE133361 | sm-PORE-cupine / PORE-cupine: NAI-N3 read by **nanopore direct RNA-seq**, so neither `RT-stop` nor `MaP` fits `principle`. Needs a schema decision before it can be curated. |
| GSE245141 | SNIPER-seq: 2'-aminodeoxycytidine + isoS-N3 isothiocyanate, no matching `chemical` enum value |
| GSE154563 | one run per (reagent, organism, context) - no biological replicates |
| GSE95567 | DMS-seq total and ribo-depleted are n=1 each; SPET-seq is the paper's own method |
| GSE226865 | targeted, and ex-virion 1M7/DMSO n=1 per serotype; in-cell arm uses SDA, no replicates |
| GSE189259 | 1 x 2A3 + 1 x DMSO per virus, no replicates |
| GSE327273 | DNA unwinding (TnpB), not RNA probing |
| GSE271937 | DNA language model, no probing data |
| GSE118387 | only the 37 C FUSE pair is replicated; every other condition n=1 |

## Remaining backlog, re-triaged against the scope gate

The 122 STRONG-signal series were re-classified after transcriptome-wide scope
became reject-gate condition (c). Per-row detail:
`full_sweep_scope_classified.tsv`.

| Class | Count | Meaning |
|---|---:|---|
| **transcriptome-wide** | **26** | genuinely in scope - the real remaining queue |
| borderline | 7 | **all 7 resolved: none curatable** (see below) |
| targeted | 71 | single RNA / amplicon / construct - **do not curate** |
| fails another gate | 5 | no replicates, titration only, or not probing |
| duplicate | 3 | same series under a zero-padded uid, or a superseries |

**So the queue is ~26 datasets, not ~115.** Roughly 60% of the
STRONG-signal hits are targeted studies: single lncRNAs, riboswitches, minigenes,
rRNA/ribosome particles and designed constructs. That is the dominant failure
mode of a keyword sweep and the scope gate is what removes it.

### Transcriptome-wide - the queue (26)

| Accession | Year | n | Note | Study |
|---|---|---|---|---|
| GSE309111 | ? | 8 | nanopore DRS structure ensembles | Direct RNA sequencing and signal alignment reveal RNA structure ensembles in a e |
| GSE288910 | ? | 126 | HeLa stress granules; DMS subsets need separating from Ribo/RNA-seq | RNA structure directs RNA partitioning and is actively disrupted inside stress g |
| GSE156671 | ? | 99 | genome-wide structure, neuronal differentiation (n=99) | Genome-wide structure changes during neuronal differentiation drive gene regulat |
| GSE304703 | ? | 8 | nanopore DRS structure ensembles (RNA004) | Direct RNA sequencing and signal alignment reveal RNA structure ensembles in a e |
| GSE304702 | ? | 105 | nanopore DRS structure ensembles, Candida albicans | Direct RNA sequencing and signal alignment reveal RNA structure ensembles in a e |
| GSE245141 | ? | 22 | transcriptome-wide probing with temporal resolution | Transcriptome-wide RNA structure probing with temporal resolution |
| GSE285333 | 2026 | 102 | multi-site DMS probing in living cells; human/E. coli/Tetrahymena | Simultaneous mapping of RNA secondary, tertiary, and quaternary structure in liv |
| GSE254264 | 2025 | 65 | CoST-seq + DMS-MaPseq, yeast, glucose/galactose, biol reps | Rapid folding of nascent RNA regulates eukaryotic RNA biogenesis |
| GSE244468 | 2025 | 42 | HIV-1 infected cells; probing arm is the viral genome | The translational landscape of HIV-1 infected cells reveals key gene regulatory  |
| GSE254895 | 2024 | 33 | new G/U reagent in vivo, E. coli, repA-C | A new reagent for in vivo structure probing of RNA G and U residues that improve |
| GSE246523 | 2024 | 4 | human mitochondrial mRNA structurome (n=4, check replication) | The human mitochondrial mRNA structurome reveals mechanisms of gene expression. |
| GSE233607 | 2023 | 9 | E. coli in-cell DMS + EDC, control/DMS/EDC rep1-3 | In vivo-like nearest neighbor parameters accurately predict fractional RNA base- |
| GSE210478 | 2022 | 6 | EBV-infected BJAB-B1 transcriptome, DMS | DMS probing of and sequencing of the EBV infected BJAB-B1 transcriptome |
| GSE154563 | 2021 | 36 | new SHAPE reagent in living cells: E. coli, B. subtilis, human | SHAPE analysis of RNA structure in living cells with unprecedented accuracy |
| GSE236224 | 2021 | 9 | genome-wide structure changes, human neurogenesis | Genome-wide RNA structure changes during human neurogenesis modulate gene regula |
| GSE149018 | 2021 | 42 | tNet-MaPseq nascent transcriptome, WT vs slow Pol II, rep1-3 | Alternative RNA Stuctures Formed During Transcription Depend on Elongation Rate  |
| GSE149767 | 2020 | 40 | SHAPE-eCLIP / fSHAPE, transcriptome-wide | Footprinting SHAPE-eCLIP reveals transcriptome-wide hydrogen bonds at RNA-protei |
| GSE103421 | 2018 | 63 | E. coli cold shock DMS-seq timecourse (drop the cspA DMS-MaPseq arm) | A stress response that monitors and regulates mRNA structure is central to cold- |
| GSE102069 | 2018 | 30 | human infection timecourse, DMS + denatured controls | Unraveling cis-regulatory elements by mapping structural changes in mRNAs |
| GSE95567 | 2017 | 41 | E. coli DMS-seq total + ribo-depleted (drop SPET-seq arm) | In vivo probing of nascent RNA structures reveals principles of cotranscriptiona |
| GSE143121 | 2012 | 57368 | ENCODE icSHAPE HepG2 - filter runs to the series GSMs | icSHAPE from HepG2 (ENCSR992XHC) |
| GSE143120 | 2012 | 57368 | ENCODE icSHAPE K562 - filter runs to the series GSMs | icSHAPE from K562 (ENCSR976RFC) |
| GSE143102 | 2012 | 57368 | ENCODE icSHAPE GM12878 - filter runs to the series GSMs | icSHAPE from GM12878 (ENCSR836VQU) |
| GSE143096 | 2012 | 57368 | ENCODE icSHAPE K562 - filter runs to the series GSMs | icSHAPE from K562 (ENCSR803XFA) |
| GSE142946 | 2012 | 57368 | ENCODE icSHAPE HepG2 - filter runs to the series GSMs | icSHAPE from HepG2 (ENCSR286LXS) |
| GSE142891 | 2012 | 57368 | ENCODE icSHAPE GM12878 - filter runs to the series GSMs | icSHAPE from GM12878 (ENCSR052BBY) |

Two structural warnings carried over: the six **ENCODE icSHAPE** series resolve to
the whole ENCODE BioProject (n=57368), so the run list must be filtered to each
series' own GSMs; and several entries are **mixed series** where the probing runs
sit alongside Ribo-seq/RNA-seq and must be separated first (`GSE288910`,
`GSE103421`, `GSE95567`).

### Borderline - RESOLVED, none curatable (7)

Each was checked against its GEO `overall_design`. All seven fail a gate:

| Accession | Verdict |
|---|---|
| GSE153303 | **not probing** - plain RNA-seq under DRB / a-amanitin elongation inhibitors; matched the sweep on a keyword |
| GSE255191 | **not probing** - translation-initiation-site mapping in cortical neurons |
| GSE228168 | NAP-seq (non-capped RNA profiling); the single SHAPE-MaP NAI-N3 pair is an add-on with no replication |
| GSE148202 | mostly DAMM-seq methylation mapping; the icSHAPE arm is an input/pulldown of mitochondrial dsRNA, not a structurome |
| GSE135211 | PAIR-MaP: RT uses random 9mers only for 16S/23S rRNA and gene-specific primers for everything else - targeted despite the "total RNA" sample names |
| GSE225730 | a defined set of T7 / native tRNAs probed inside peptide droplets in vitro, not a cellular tRNA structurome |
| GSE133361 | PORE-cupine - genuine transcriptome-wide probing of H9 cells, but read out by **nanopore**; parked with the sm-PORE-cupine series below pending a `principle` enum decision |

### Targeted - out of scope, do not curate (71)

Kept only so a future sweep does not re-surface them as new.

| Accession | Year | n | Note | Study |
|---|---|---|---|---|
| GSE230167 | ? | 3 | single RNA / amplicon / construct | Structural basis for pre-miRNA-31 biogenesis |
| GSE183045 | ? | 64 | SSU processome rRNA | Using DMS-MaPseq to dissect structural differences of ribosomal RNA in different |
| GSE327654 | ? | 6 | single RNA / amplicon / construct | CONCR lncRNA organizes a 3´-end structural domain that engages DDX11 for DNA rep |
| GSE331520 | ? | 37 | single RNA / amplicon / construct | Conserved structural features of the lncRNA HOTAIR in breast cancer cells |
| GSE309440 | ? | 28 | single RNA / amplicon / construct | Probing the structure of the lncRNA DAMER and its interaction with ATF4 mRNA usi |
| GSE149534 | ? | 16 | single RNA / amplicon / construct | Long noncoding RNA CCTT recruits CENP-C to centromeres by directly binding to ce |
| GSE149529 | ? | 6 | single RNA / amplicon / construct | Long noncoding RNA CCTT recruits CENP-C to centromeres by directly binding to ce |
| GSE130687 | ? | 32 | HIV-1 5UTR | An epitranscriptomic switch at the 5´-UTR controls genome selection during HIV-1 |
| GSE81525 | ? | 36 | SERPINA1 constructs | An RNA structure-mediated post-transcriptional model of α-1-antitrypsin deficien |
| GSE225383 | ? | 73 | RNase P / RMRP | Enhanced DMS-MaP enables superior RNA structural analysis |
| GSE273118 | ? | 28 | ModT ncRNA | A conserved structured non-coding RNA coordinates growth and virulence in Clostr |
| GSE255779 | 2025 | 8 | 18S rRNA | The integrated stress response finetunes 18S nonfunctional rRNA decay (DMS-MaPse |
| GSE256185 | 2025 | 122 | single RNA / amplicon / construct | Quantitative profiling of human translation initiation reveals elements that pot |
| GSE239954 | 2025 | 93 | single RNA / amplicon / construct | Characterization of group I introns in generating circular RNAs as vaccines |
| GSE283716 | 2025 | 89 | single RNA / amplicon / construct | Structural determinants of inverted Alu-mediated backsplicing revealed by -MaP a |
| GSE248680 | 2025 | 40 | single RNA / amplicon / construct | Therapeutic application of circular RNA aptamers in a mouse model of psoriasis |
| GSE248679 | 2025 | 22 | EPIC circRNA constructs | circSHAPE-MaP of EPIC |
| GSE246246 | 2025 | 6 | engineered circRNA constructs | NicOPURE: Nickless RNA Circularization and One-Step Purification with Engineered |
| GSE264057 | 2025 | 9 | translational enhancer constructs | Cellular translational enhancer elements that recruit eukaryotic initiation fact |
| GSE279023 | 2025 | 4 | JUN / EGFR 5UTR | Functional screen for mediators of onco-mRNA translation specificity [II] |
| GSE255740 | 2025 | 6 | MYC 5UTR | Functional screen for mediators of onco-mRNA translation specificity [DMS-seq] |
| GSE188445 | 2025 | 47 | single RNA / amplicon / construct | Structural features within the NORAD long noncoding RNA underlie efficient repre |
| GSE255784 | 2025 | 46 | 18S rRNA | The integrated stress response finetunes 18S nonfunctional rRNA decay |
| GSE283338 | 2025 | 68 | single RNA / amplicon / construct | Proximity mediated effects of RNA regulatory proteins (mRNA as a proxisome). |
| GSE286293 | 2025 | 41 | group II intron / RNase P / TPP constructs | A Small Cationic Probe for Accurate, Punctate Discovery of RNA Tertiary Structur |
| GSE230495 | 2025 | 32 | F8 exon 16 variants | OpenASO: RNA Rescue-designing splice-modulating antisense oligonucleotides throu |
| GSE220470 | 2024 | 8 | 15.5K-bound RNAs (RIP) | RIP-PEN-SHAPE-MaP for 15.5K-interacted RNAs |
| GSE228970 | 2024 | 33 | single RNA / amplicon / construct | Promotion of TLR7-MyD88-dependent Inflammation and Autoimmunity through Stem-loo |
| GSE243220 | 2024 | 16 | single RNA / amplicon / construct | In-cell structure analysis of antisense Gadd45α SINEB2-a deletion mutants |
| GSE224534 | 2024 | 20 | single RNA / amplicon / construct | In-cell RNA secondary structure analysis of functional SINE transcripts |
| GSE219083 | 2024 | 54 | single RNA / amplicon / construct | G-quadruplex folding in Xist RNA antagonizes PRC2 activity for step-wise regulat |
| GSE219079 | 2024 | 24 | single RNA / amplicon / construct | Epigenetic regulation by dynamic RNA G-quadruplex folding and unfolding (DMS-Seq |
| GSE271825 | 2024 | 30 | AKT2 / pUG / Spinach constructs | RNA tertiary structure and conformational dynamics revealed by BASH MaP |
| GSE191144 | 2023 | 16 | single RNA / amplicon / construct | Investigating the NRAS 5’ UTR as a Target for Small Molecules |
| GSE196625 | 2023 | 30 | pre-rRNA amplicons | URB1 ensures 3' end processing of pre-rRNAs to prevent exosome-dependent degrada |
| GSE210296 | 2022 | 8 | OsNRT2.3 / OsNRT1.1B | High-temperature adaptation of an OsNRT2.3 allele is thermoregulated by small RN |
| GSE188649 | 2022 | 11 | AdML minigene | [SHAPE-MaP_4_mM] U1 snRNP regulates recruitment of early spliceosomal components |
| GSE163112 | 2022 | 4 | single RNA / amplicon / construct | Enhancer RNAs make multivalent interactions with NELF to stimulate Pol II pause  |
| GSE174217 | 2022 | 20 | single RNA / amplicon / construct | Distinct MUNC lncRNA structural domains regulate transcription of different prom |
| GSE190787 | 2022 | 12 | single RNA / amplicon / construct | A disease-linked lncRNA mutation in RNase MRP inhibits ribosome synthesis [RMRP_ |
| GSE171021 | 2022 | 24 | single RNA / amplicon / construct | A disease-linked lncRNA mutation in RNase MRP inhibits ribosome synthesis |
| GSE183941 | 2022 | 32 | single RNA / amplicon / construct | RNA circles with minimized immunogenicity as potent PKR inhibitors. |
| GSE160161 | 2021 | 108 | pre-40S rRNA | Using DMS-MaPseq to dissect structural differences of ribosomal RNA in different |
| GSE147506 | 2021 | 20 | single RNA / amplicon / construct | Key role of dysregulated SF3A3 translation in MYC-induced breast tumorigenesis |
| GSE147504 | 2021 | 5 | single RNA / amplicon / construct | Targeted DMS probing of SF3A3 5' UTR |
| GSE168393 | 2021 | 4 | yvrE / ctc genes | Translational activation by an alternative sigma factor in Bacillus subtilis |
| GSE183927 | 2021 | 16 | single RNA / amplicon / construct | ANKRD52_SHAPE-MaP |
| GSE159719 | 2021 | 13 | one low-abundance pre-mRNA | RNA structure probing to characterize RNA-protein interations on a low abundance |
| GSE173177 | 2021 | 9 | AdML minigene | Discovery of pre-mRNA structural scaffold as a contributor to mammalian splicing |
| GSE173175 | 2021 | 50 | AdML minigene | Discovery of a pre-mRNA structural scaffold as a contributor to the mammalian sp |
| GSE174140 | 2021 | 12 | single RNA / amplicon / construct | lncRNA SLERT controls phase separation of FC/DFCs to facilitate Pol I transcript |
| GSE163494 | 2021 | 4 | pasRNA_ABAT | Shape of promoter antisense RNAs regulates ligand-induced transcription activati |
| GSE152483 | 2021 | 87 | RNase P, XIST, U1, Rmrp | Analysis of RNA-protein networks with RNP-MaP defines functional hubs on RNA. |
| GSE162569 | 2020 | 27 | SARS-CoV-2 fragments, not the genome | Genomic RNA elements drive phase separation of the SARS-CoV-2 nucleocapsid |
| GSE156312 | 2020 | 99 | aptamer + small molecule | PEARL-seq: A Photoaffinity Platform for the Analysis of Small Molecule-RNA Inter |
| GSE140048 | 2020 | 20 | single RNA / amplicon / construct | SHAPE and DMS probing of SLNCR1 lncRNA conserved region 403-780 |
| GSE146407 | 2020 | 8 | single RNA / amplicon / construct | In vivo structure analysis of SINEUP RNA |
| GSE149061 | 2020 | 6 | polyA constructs / HIV 3UTR | Anomalous Reverse Transcription through Chemical Modifications in Polyadenosine  |
| GSE118309 | 2019 | 42 | 7SK, Xist fragments | Carbodiimide reagents for the chemical probing of RNA structure in cells |
| GSE108857 | 2018 | 6 | single RNA / amplicon / construct | SWI/SNF subunit CHR2 remodels pri-miRNAs via microprocessor component SE to inhi |
| GSE110516 | 2018 | 8 | pre-let-7 | secondary structure based on icSHAPE of pre-let-7 and hDicer-TRBP  bound pre-let |
| GSE105112 | 2018 | 12 | 30S ribosome variants | Structural characterization of ribosome variants |
| GSE109652 | 2018 | 16 | single RNA / amplicon / construct | Transcription elongation rate affects nascent histone pre-mRNA folding and 3' en |
| GSE106868 | 2018 | 6 | single RNA / amplicon / construct | Maturation of the 90S pre-ribosome requires Mrd1 dependent U3 snoRNA and 35S pre |
| GSE97609 | 2017 | 20 | 18S rRNA | Interpreting reverse transcriptase termination and mutation events for greater i |
| GSE85619 | 2017 | 8 | 80S ribosome | Inhibition of eukaryotic translation by the antitumor natural product Agelastati |
| GSE72599 | 2016 | 12 | single RNA / amplicon / construct | 7SK-BAF axis controls pervasive transcription at enhancers [icShape] |
| GSE69143 | 2016 | 74 | single RNA / amplicon / construct | 7SK-BAF axis controls pervasive transcription at enhancers |
| GSE67667 | 2015 | 13 | single RNA / amplicon / construct | Probing Xist RNA structure in cells using Targeted Structure-Seq |
| GSE067667 | 2015 | 13 | single RNA / amplicon / construct | Probing Xist RNA Structure in Cells Using Targeted Structure-Seq. |
| GSE052878 | 2014 | 41 | pre-rRNA 40S | Snapshots of pre-rRNA structural flexibility reveal eukaryotic 40S assembly dyna |

### Fails another gate (5) / duplicates (3)

| Accession | Year | n | Note | Study |
|---|---|---|---|---|
| GSE115159 | 2020 | 6 | DMS concentration titration, not biological replicates | Regulation of Translation Elongation Revealed by Ribosome Profiling [Dataset_2] |
| GSE115158 | 2020 | 15 | DMS concentration titration, not biological replicates | Regulation of Translation Elongation Revealed by Ribosome Profiling [Dataset_1] |
| GSE143496 | 2020 | 25 | ribo-depleted RNA-seq, not probing | Species-specific processing of long noncoding RNAs contributes to non-conserved  |
| GSE122199 | 2019 | 104 | piRNA IP + RNA-seq, not probing | Planarians recruit piRNAs for mRNA turnover in adult stem cells |
| GSE111962 | 2018 | 2 | transcriptome-wide but only 2 runs, no replicates | RNA Framework: an all-in-one toolkit for the analysis of RNA structures and post |

| Accession | Year | n | Note | Study |
|---|---|---|---|---|
| GSE100715 | 2018 | 32 | superseries of GSE100714, already curated as 00081 | Genome-wide RNA structurome reprogramming by acute heat shock globally regulates |
| GSE083821 | 2017 | 22 | same as GSE83821 (removed as targeted) | High-throughput RNA structure probing reveals critical folding events during ear |
| GSE097609 | 2017 | 20 | same as GSE97609 | Interpreting Reverse Transcriptase Termination and Mutation Events for Greater I |

## Notes for whoever works this queue

- Several superseries/subseries pairs are both listed - curate the probing
  **subseries** (e.g. `GSE100714` not `GSE100715`).
- Duplicate-looking pairs with a leading zero (`GSE83821`/`GSE083821`,
  `GSE97609`/`GSE097609`) are the same series; the zero-padded form is an artefact
  of the GEO uid mapping.
- The `NONE` bucket (111 series) carries a lot of literature-elink noise (papers
  matched on "PARS" or "mutational profiling" that are not RNA probing at all).
  It is not automatically out of scope, but it is low-yield.
