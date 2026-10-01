# Open leads

Rewritten at the end of every sweep: still-open rows carried forward plus new
uncurated candidates. Curated leads leave the table; rejected ones go to
`../excluded_dois.tsv` first. History is in git.

Last sweep: 2026-10-01, literature only, all years (2,060 new papers, 186 with an
accession; no new leads, 52 rejects added to `../excluded_dois.tsv`). Last GEO sweep:
2026-09-24 (410 series).

| Accession | DOI | Why it is waiting |
|---|---|---|
| GSE200706 | 10.1038/s41467-023-35811-x | n=1; special case: in-cell control vs starved, in vitro K+ vs Li+ |
| GSE154563 | — | one run per reagent/organism/context; special case: new SHAPE reagent in *E. coli*, *B. subtilis*, human |
| GSE95567 | — | DMS-seq total / ribo-depleted n=1; weak special case (drop SPET-seq) |
| GSE223117 | 10.1093/nar/gkae185 | human NAI-N3 + DMSO, n=1; weak: no special condition |
| GSE111962 | — | 2 runs; weak: no special condition |
| GSE189259 | — | one 2A3 + one DMSO per virus; special case if whole viral genomes |
| PRJNA936272 | 10.1128/jvi.00635-23 | native SARS-CoV-2 stem-loop II, WT and s2m mutant, n=1 |
| GSE226865 | — | viral region, n=1: check which arms are native viral RNA |
| PRJNA669862 | 10.3390/v12121473 | SARS-CoV-2 3'UTR in virions: isolate not stated (BioSample says "cDNA clone") |
| PRJNA554838 | 10.1093/nar/gkz1124 | Flock House virus in virions: one DMS pair only |
| PRJNA725417 | 10.1080/15476286.2022.2058818 | BVDV IRES transcribed in vitro: native sequence or construct? |
| GSE162569 | — | SARS-CoV-2 wild-type fragments in vitro, 5NIA, one run per region |
| GSE78208 | — | yeast NAI in vivo x2; protocol says both rRNA-depleted and rRNA libraries |
| GSE157014 | — | E. coli nascent rRNA (4sU pulldown) DMS, mostly n=1 time course |
| PRJNA553663 | 10.1371/journal.pbio.3000393 | E. coli in-cell DMS +/- rifampicin/spectinomycin, rRNA focus |
