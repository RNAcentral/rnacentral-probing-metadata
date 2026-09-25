# Open leads

Last sweep: 2026-09-24, second pass (all years; literature 2,097 new papers, GEO 410 series).

Replication stopped being a hard reject and native viral regions became in scope on
2026-09-24, so these earlier rejects are candidates again. Curated so far: rnastruct00109-00120.

| Accession | DOI | Earlier reason | Now |
|---|---|---|---|
| GSE200706 | 10.1038/s41467-023-35811-x | n=1 | special case: in-cell control vs starved, in vitro K+ vs Li+ |
| GSE154563 | — | one run per reagent/organism/context | special case: new SHAPE reagent in *E. coli*, *B. subtilis*, human |
| GSE95567 | — | DMS-seq total / ribo-depleted n=1 | weak special case (drop SPET-seq) |
| GSE223117 | 10.1093/nar/gkae185 | human NAI-N3 + DMSO, n=1 | weak: no special condition |
| GSE111962 | — | 2 runs | weak: no special condition |
| GSE189259 | — | one 2A3 + one DMSO per virus | special case if whole viral genomes |
| PRJNA936272 | 10.1128/jvi.00635-23 | viral region | native: SARS-CoV-2 stem-loop II, WT and s2m mutant, n=1 |
| GSE226865 | — | viral region, n=1 | check which arms are native viral RNA |

## From the 2026-09-24 second sweep

Curated: rnastruct00121-00137, plus GSE264642 added to rnastruct00066. Rejected (in
`../excluded_dois.tsv`, or GEO-only): GSE108859 (targeted), GSE338022 (purified ribosome
particles), GSE291931 (DNA mutagenesis, not probing), GSE252404 (dbGaP only), PRJNA865760
(already rnastruct00084).

Still open:

| Accession | DOI | Why it is waiting |
|---|---|---|
| PRJNA669862 | 10.3390/v12121473 | SARS-CoV-2 3'UTR in virions: isolate not stated (BioSample says "cDNA clone") |
| PRJNA554838 | 10.1093/nar/gkz1124 | Flock House virus in virions: one DMS pair only |
| PRJNA725417 | 10.1080/15476286.2022.2058818 | BVDV IRES transcribed in vitro: native sequence or construct? |
| GSE162569 | — | SARS-CoV-2 wild-type fragments in vitro, 5NIA, one run per region |
| GSE78208 | — | yeast NAI in vivo x2; protocol says both rRNA-depleted and rRNA libraries |
| GSE157014 | — | E. coli nascent rRNA (4sU pulldown) DMS, mostly n=1 time course |
| PRJNA553663 | 10.1371/journal.pbio.3000393 | E. coli in-cell DMS +/- rifampicin/spectinomycin, rRNA focus |

Rejected and recorded in `../excluded_dois.tsv`: nanopore PORE-cupine series
(GSE133361, GSE304702, GSE304703, GSE309111), SNIPER-seq (GSE245141, chemicals not in
the schema), PRJEB44384 (no runs on ENA), and viral constructs (`scope-viral`).
