# Open leads

Last sweep: 2026-09-24 (full history, all years, literature + GEO).

Replication stopped being a hard reject and native viral regions became in scope on
2026-09-24, so these earlier rejects are candidates again. None is curated yet.

| Accession | DOI | Earlier reason | Now |
|---|---|---|---|
| PRJNA946372 | 10.1038/s41592-023-02128-y | technical replicates only | special case: bulk / 100-cell / 10-cell hESC and neurons |
| GSE200706 | 10.1038/s41467-023-35811-x | n=1 | special case: in-cell control vs starved, in vitro K+ vs Li+ |
| GSE103421 | — | timepoints n=1 | special case: *E. coli* cold-shock DMS-seq timecourse (drop cspA amplicons) |
| GSE154563 | — | one run per reagent/organism/context | special case: new SHAPE reagent in *E. coli*, *B. subtilis*, human |
| GSE149018 | — | WT tNet-MaPseq arm n=1 | partial replication: WT vs slow Pol II (drop enzymatic PIPseq arm) |
| GSE118387 | — | only 37 C FUSE pair replicated | partial replication |
| GSE95567 | — | DMS-seq total / ribo-depleted n=1 | weak special case (drop SPET-seq) |
| GSE223117 | 10.1093/nar/gkae185 | human NAI-N3 + DMSO, n=1 | weak: no special condition |
| GSE111962 | — | 2 runs | weak: no special condition |
| GSE115158, GSE115159 | — | DMS concentration titrations | titration, like 00024 |
| GSE189259 | — | one 2A3 + one DMSO per virus | special case if whole viral genomes |
| PRJNA1443375 | 10.1128/jvi.00898-26 | viral region | native: sfRNA in infected cells and in vitro |
| PRJNA936272 | 10.1128/jvi.00635-23 | viral region | native: SARS-CoV-2 stem-loop II, WT and s2m mutant, n=1 |
| PRJNA955716 | 10.1073/pnas.2320782121 | viral region | native: bocavirus BocaSR |
| GSE244468 | — | viral region | native: HIV-1 frameshift site in infected cells |
| GSE226865 | — | viral region, n=1 | check which arms are native viral RNA |

Rejected and recorded in `../excluded_dois.tsv`: nanopore PORE-cupine series
(GSE133361, GSE304702, GSE304703, GSE309111), SNIPER-seq (GSE245141, chemicals not in
the schema), PRJEB44384 (no runs on ENA), and viral constructs (`scope-viral`).
