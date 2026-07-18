# Per-candidate curation prompt (one subagent per paper)

Spawn a `general-purpose` subagent per shortlisted candidate. Fill in the four
`<...>` placeholders. The subagent produces one validated YAML or a REJECT line.

---

You are curating ONE RNA chemical-probing dataset into a metadata YAML for the repo
at `<REPO_ABS_PATH>` (this is your cwd). Work ONLY in that repo and modify ONLY the
one new YAML you create. Do NOT run git.

CANDIDATE:
- DOI: `<DOI>`
- Data accession (from the candidate table): `<ACCESSION>`
- Description: `<ONE_LINE>`
- Assigned dataset_id: `<rnastruct#####>`

READ FIRST (only these, to learn conventions): `docs/template.yaml`,
`DMS/rnastruct00065.yaml`, `SHAPE/rnastruct00066.yaml`. For viral datasets also read
one existing file that has a `strain:` field.

STEPS:
1. Resolve PMCID + open-access flag:
   `curl -s 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%22<DOI>%22&format=json&resultType=lite' | python3 -c "import sys,json;r=json.load(sys.stdin)['resultList']['result'][0];print(r.get('pmcid'),r.get('isOpenAccess'))"`
   Then download the full text to a temp file and GREP it (never read the whole XML
   into context):
   `curl -s 'https://www.ebi.ac.uk/europepmc/webservices/rest/<PMCID>/fullTextXML' -o /tmp/<id>.xml`
   Grep for: the probing method, the chemical probe, the RT enzyme, pH, in
   vivo/in vitro/in virio, virus strain (if viral), and the **data-availability**
   paragraph. CONFIRM `<ACCESSION>` is THIS study's OWN data, not a cited/re-used
   dataset. If it is re-used, find the study's real accession.
2. Get the run list: `.venv/bin/python .claude/skills/rnacentral-probing-finder/scripts/expand_accession.py <ACCESSION> --tsv`
   (run accession + sample title). Identify which runs are probing vs plain
   RNA-seq / MeRIP / functional-screen, and use only the probing runs.
3. DECISION — qualifies ONLY IF (a) genuine chemical probing (SHAPE or DMS family)
   AND (b) each treated `sample_group` has ≥2 biological replicates (a titration or
   time-course is NOT biological replication). If not, write NO file and return
   exactly: `REJECT <rnastruct#####>: <one-line reason>`.
4. If it qualifies, fill a copy of `docs/template.yaml` at `<folder>/<rnastruct#####>.yaml`
   (`DMS/` if the chemical is DMS; `SHAPE/` for a SHAPE reagent). Follow the
   field-mapping rules in the parent SKILL.md exactly, especially:
   - `rna_type` MUST be `mRNA`/`total`/`sRNA` (null FAILS); default `total`.
   - `obi` must match `chemical` (DMS=OBI:0001015, NAI=OBI:0003886, NAI-N3=OBI:0003887,
     1M7=OBI:0003885, 2A3=OBI:0003888, NMIA=OBI:0001026, 1M6=OBI:0003895,
     5NIA=OBI:0003896; else null).
   - `RT_enzyme`: TGIRT/Marathon/group II → `Group II intron`; SuperScript/Maxima →
     `M-MLV` (ignore "M-MLV buffer" red herrings).
   - `principle`: RT-stop (truncation) vs MaP (mutational profiling).
   - `condition`: no-probe/DMSO/(−)reagent → untreated; probe → treated; heat →
     denatured. `sample_group`: no whitespace, underscores.
   - Viral: NCBI common name + top-level `strain:` (schema pattern rejects trailing
     digits in `scientific_name` — use the validating parent name).
   - `comment: null`.
5. Validate and fix until clean:
   `.venv/bin/linkml-validate -s schema/rnastruct.schema.yaml <folder>/<rnastruct#####>.yaml`
   (must say "No issues found"),
   `.venv/bin/python scripts/validate_obi_ids.py <folder>/<rnastruct#####>.yaml`,
   `.venv/bin/python scripts/validate_ncbi_taxonomy.py <folder>/<rnastruct#####>.yaml`.
6. RETURN a one-paragraph summary: id, folder, doi, accession, organism,
   method/chemical/principle/RT_enzyme, #runs, #sample_groups, replicate structure,
   and validation status. OR the REJECT line.
