nextflow.enable.dsl = 2

params.repo_dir = null
params.ids_dir = null
params.outdir = null
params.fetchngs_revision = "1.13.0"
params.fetchngs_profile = "slurm"
params.nxf_singularity_cachedir = null
params.dataset_id = null  // optional: process only this dataset (e.g. rnastruct00001)

process VALIDATE_AND_GENERATE {
  tag "validate-and-generate"
  executor "local"

  input:
  val repo_dir
  val ids_dir
  val dataset_id

  output:
  path "ids_manifest.txt", emit: ids_manifest

  script:
  def dataset_env = dataset_id ? "DATASET_ID=\"${dataset_id}\"" : ""
  """
  set -euo pipefail

  mkdir -p "${ids_dir}"

  (
    cd "${repo_dir}"
    IDS_DIR="${ids_dir}" ${dataset_env} bash scripts/validate_and_generate.sh
  )

  find "${ids_dir}" -maxdepth 1 -type f -name '*.csv' | sort > ids_manifest.txt

  if [ ! -s ids_manifest.txt ]; then
    echo "ERROR: no CSV files were generated in ${ids_dir} (datasets whose comment starts with 'failed QC' or 'skip' produce no CSV)" >&2
    exit 1
  fi
  """
}

process RUN_FETCHNGS {
  tag "run-fetchngs"
  executor "local"

  input:
  path ids_manifest
  val repo_dir
  val outdir
  val fetchngs_revision
  val fetchngs_profile
  val nxf_singularity_cachedir

  output:
  val true, emit: fetch_complete

  script:
  """
  set -euo pipefail

  mkdir -p "${outdir}"
  export NXF_SINGULARITY_CACHEDIR="${nxf_singularity_cachedir}"

  while IFS= read -r ids_file; do
    [ -n "\${ids_file}" ] || continue

    sample_name="\$(basename "\${ids_file}" .csv)"
    sample_outdir="${outdir}/\${sample_name}"
    existing_samplesheet="\${sample_outdir}/samplesheet/samplesheet.csv"

    if [ -s "\${existing_samplesheet}" ]; then
      echo "Skipping \${ids_file}; dataset already present at \${existing_samplesheet}."
      continue
    fi

    mkdir -p "\${sample_outdir}"

    nextflow run nf-core/fetchngs -r "${fetchngs_revision}" \
      -c "${repo_dir}/nextflow.config" \
      -profile "${fetchngs_profile}" \
      --input "\${ids_file}" \
      --outdir "\${sample_outdir}" \
      -resume
  done < "${ids_manifest}"

  """
}

process MERGE_FETCHNGS_METADATA {
  tag "merge-fetchngs-metadata"
  executor "local"

  input:
  val _fetch_done
  val repo_dir
  val outdir

  output:
  path "rnastruct_samplesheets_manifest.txt", emit: rnastruct_manifest

  script:
  """
  "${repo_dir}/scripts/merge_fetchngs_metadata.sh" "${repo_dir}" "${outdir}"
  cp "${outdir}/samplesheet/rnastruct_samplesheets_manifest.txt" rnastruct_samplesheets_manifest.txt
  """
}

workflow {
  // Fail early with clear messages if required paths are not provided.
  def requiredParams = ["repo_dir", "ids_dir", "outdir", "nxf_singularity_cachedir"]
  requiredParams.each { param ->
    if (!params[param]) {
      error "Missing required parameter: --${param}. Copy nextflow.config.example to nextflow.config and fill in the paths."
    }
  }

  validate = VALIDATE_AND_GENERATE(params.repo_dir, params.ids_dir, params.dataset_id ?: "")
  fetch = RUN_FETCHNGS(
    validate.ids_manifest,
    params.repo_dir,
    params.outdir,
    params.fetchngs_revision,
    params.fetchngs_profile,
    params.nxf_singularity_cachedir
  )
  MERGE_FETCHNGS_METADATA(
    fetch.fetch_complete,
    params.repo_dir,
    params.outdir
  )
}
