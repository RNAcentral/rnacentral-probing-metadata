# Per-candidate curation prompt

Give one `general-purpose` subagent this text per candidate, with the `<…>` filled in.

---

Curate ONE RNA chemical-probing dataset into a metadata YAML in the repo at
`<REPO_ABS_PATH>` (your cwd). Create only that one file; don't run git.

- DOI: `<DOI>`
- Accession: `<ACCESSION>`
- Description: `<ONE_LINE>`
- dataset_id: `<rnastruct#####>`

Rules: `.claude/skills/rnacentral-probing-finder/SKILL.md` — read "Gate",
"Field mapping", "Naming", "Control pairing" and "Where notes go"; they override
anything below. Examples: `docs/template.yaml`, `DMS/rnastruct00090.yaml`,
`SHAPE/rnastruct00096.yaml`; for viral data also `SHAPE/rnastruct00101.yaml`.

1. Get the PMCID and open-access flag:
   `curl -s 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%22<DOI>%22&format=json&resultType=lite'`.
   Fetch the full text to a file (SKILL.md step 3.1) and **grep** it for method,
   probe, RT enzyme, pH, context, strain, and the data-availability paragraph.
   Confirm `<ACCESSION>` is this study's own data; if not, find the real one.
2. `.venv/bin/python .claude/skills/rnacentral-probing-finder/scripts/expand_accession.py <ACCESSION> --tsv`
   and keep only the probing runs.
3. If gate (a) or (c) fails, write nothing and return exactly
   `REJECT <rnastruct#####>: <one-line reason>`. If only replication (b) falls
   short, curate anyway and list the unreplicated groups in your summary.
4. Otherwise write `<DMS|SHAPE>/<rnastruct#####>.yaml` from the template and run
   every check in SKILL.md "Validate" until clean.
5. Return one paragraph: id, folder, DOI, accession, organism, method / chemical /
   principle / RT_enzyme, run and group counts, replicate layout, anything
   excluded, validation status.
