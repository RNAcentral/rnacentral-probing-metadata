# Pending (paywalled) probing datasets

Stub YAMLs for chemical-probing papers whose full text Europe PMC cannot read
(`isOpenAccess: N`, no PMCID), so the data accession could not be resolved
automatically. Each file is pre-filled with everything derivable from the title,
abstract and NCBI links; everything else is marked `TODO` and the `comment:`
field says exactly what is missing.

These files are **deliberately outside `DMS/` and `SHAPE/`** — they do not
validate against `schema/rnastruct.schema.yaml` yet (placeholder `dataset_id`
and `run_accessions`), so keeping them here leaves CI green.

## Workflow

1. Open the paper (needs journal access) and read the data-availability section.
2. Fill in the accession, then expand it into runs:
   `.venv/bin/python .claude/skills/rnacentral-probing-finder/scripts/expand_accession.py <GSE|PRJNA> --tsv`
3. Fill the remaining `TODO`s using the field-mapping rules in
   `.claude/skills/rnacentral-probing-finder/SKILL.md`.
4. Apply the reject gate: genuine SHAPE/DMS-family probing **and** every treated
   `sample_group` has ≥2 biological replicates **and** transcriptome-wide scope
   (a whole viral genome counts; a single lncRNA/mRNA/riboswitch/amplicon does
   not). Four stubs were already dropped on the scope rule: SARS-CoV-2 5'UTR
   stem-loops, flavivirus sfRNA, *Physcomitrium* telomerase RNA, and the DEAD-box
   ribosome-assembly chapter.
5. Set `comment: null`, give it the next free `rnastruct#####`, move it into
   `DMS/` or `SHAPE/`, and run the four validators.
