# RNAcentral chemical probing metadata

Metadata for structural chemical probing experiments for RNAcentral.

This repository stores metadata YAML files for chemical probing datasets (for example in `SHAPE/` and `DMS/`) that are validated with [LinkML](https://linkml.io) via GitHub Actions. Once a YAML file is accepted, the pipeline downloads FASTQ files using `nf-core/fetchngs` and creates a final `samplesheet.csv` that can be used as input for `nf-core/rnastructurome`.

## Adding a new metadata YAML via pull request

To add a new dataset to this repository:

1. Clone this repository to your local machine.
2. Create a new branch from master with a descriptive name including “Add” (e.g. Add-new-shape-dataset).
3. Create a new YAML file (see section below) in the appropriate directory (for example `SHAPE/` or `DMS/`) and populate it according to the schema requirements.
4. Open a pull request with that new YAML file.
5. Wait for the GitHub Actions checks to validate the YAML.
6. If the checks pass, someone from RNAcentral will review and merge the pull request.
7. If the checks fail, inspect the GitHub Actions logs, fix the reported issue in the YAML, and update the pull request.

Note that **biological replication is required.** Each treated `sample_group` must have at least 2 biological replicates. Datasets that do not meet this criterion will not be accepted. Rare exceptions may be considered for datasets that probe a large number of biologically distinct conditions — for example, many different cell lines, subcellular fractions, or developmental stages — where the breadth of coverage partially compensates for the absence of within-group replication. Please include a justification in the pull request description if required.

## Creating a new YAML file

A fully annotated template with inline field descriptions is available at [`docs/template.yaml`](docs/template.yaml). Use it as your starting point.

1. Start from the template: copy [`docs/template.yaml`](docs/template.yaml) and rename it. If your dataset includes multiple organisms, create one YAML file per organism (e.g. one for Homo sapiens, one for Mus musculus).

2. Choose a dataset id that is a consecutive number from the last one in the repo (e.g. rnastruct00010). Check both DMS/ and SHAPE/ to find the latest id number.

3. You must also include the metadata schema version (`schema_version: "1.0.0"`), organism name, the method (which can be SHAPE or DMS variants) and principal (RT-stop or MaP) of this experiement, a publication DOI, and fill out the raw_data section. For non-viral datasets, use the Latin name (e.g. Homo sapiens). For viral datasets, use the common virus name used by NCBI Taxonomy rather than a Latin name. For viral datasets only, the strain field is also required.

4. Each sample listed under run_accessions should include a biologically meaningful and distinguishable sample_name, along with sample_group (no white spaces), condition (one of untreated, treated, or denatured), and replicate (just a number). The sample accession id must be supported by nf-core/fetchngs (e.g. SRA, ENA, DDBJ, GEO; [see the fetchngs documentation for the full list](https://nf-co.re/fetchngs/1.12.0/docs/usage)).

5. The `sample_group` field is the per-sample grouping label in the final samplesheet. Samples sharing the same `sample_group` value are analysed together. It is not limited to cell lines — use it to encode any biologically meaningful grouping, such as organism strain, tissue or developmental stage, genotype, `in_vivo`/`in_vitro` context, viral isolate, drug treatment, or perturbation. Use underscores instead of whitespace.
   - Examples from current metadata include `K562_in_vivo` and `K562_in_vitro` to distinguish sample context, and `embryonic_64c_CHX` or `embryonic_64c_PatA` to distinguish developmental stage and drug treatment.

6. The optional `rna_type` field describes what RNA fraction was captured for library preparation. Use one of `mRNA` (polyadenylated mRNA selected with oligo-dT), `total` (total or rRNA-depleted RNA, no poly-A selection), or `sRNA` (small RNA, typically <200 nt).

7. If including an OBI id, use a valid term from the [Ontology for Biomedical Investigations](http://obi-ontology.org/) / [obi-ontology/obi](https://github.com/obi-ontology/obi). If the experimental context is provided, it must be one of in_vivo, in_vitro, denatured, ex_vivo, in_virio or ex_virio.

8. All other fields are optional and can be set to null if not available.

## Installation

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) then run:

```bash
uv sync --dev
```

To run the tests:

```bash
uv run pytest
```

## Running the Nextflow pipeline

Before running the pipeline, make sure the paths in `nextflow.config` are set for your environment.

To run `main.nf` for all metadata YAML files:

```bash
nextflow run main.nf -resume
```

To run `main.nf` for a single dataset, pass the dataset ID. This is the YAML filename without the `.yaml` extension, for example `rnastruct00001`:

```bash
nextflow run main.nf --dataset_id rnastruct00001 -resume
```

## Metadata schema checks

The validator (`linkml-validate` against `schema/rnastruct.schema.yaml`) makes sure the minimum required fields for running the pipeline end-to-end are present. 
The required fields are: 
- `dataset_id`, which must match the `rnastruct00001` naming convention
- `schema_version`, which must be the current metadata schema version (`1.0.0`)
- `organism`, using the Latin name format for non-viral datasets and the common virus name used by NCBI Taxonomy for viral datasets
- `experiment.method`, which must contain `SHAPE` or `DMS`
- `experiment.principle`, which must be `RT-stop` or `MaP`
- `publication.doi`
- `raw_data.repository`, which must be one of `SRA`, `ENA`, `GEO`, or `DDBJ`
- `raw_data.accession`
- `raw_data.run_accessions`, where each item must include `accession`, `sample_name`, `sample_group`, `condition`, and `replicate`
  - `sample_group` must not contain white spaces — use underscores instead (e.g. `embryonic_cells`, not `embryonic cells`)

All other fields are optional and, if not known, can be `null`.

For viral datasets the optional top-level field `strain` should be provided and should describe the strain hared by all samples in the dataset. This field is not required for non-viral datasets. If a viral study includes multiple strains create one YAML file per strain.
The optional field `experiment.context`, when provided, must use one or more of: `in_vivo`, `in_vitro`, `ex_vivo`, `in_virio`, `ex_virio`, or `denatured`.

## GitHub Actions checks

The `Validate Metadata` GitHub Actions workflow validates metadata files with these checks:

1. Validates each selected YAML file against the metadata schema.
2. Checks uniqueness of dataset IDs and run accession IDs across all metadata files.
3. Validates OBI IDs.
4. Validates viral strains by checking if it exists in NCBI taxonomy.
