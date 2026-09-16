#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_dir}"

schema="schema/rnastruct.schema.yaml"
# Allow callers (e.g. Slurm wrapper) to override where ID CSVs are written.
output_dir="${IDS_DIR:-${repo_dir}/ids}"
# Optional: restrict processing to a single dataset (e.g. DATASET_ID=rnastruct00001).
dataset_filter="${DATASET_ID:-}"

if ! command -v linkml-validate >/dev/null 2>&1; then
  echo "linkml-validate not found. Install with: pip install linkml" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found in PATH." >&2
  exit 1
fi

shopt -s nullglob
shape_yamls=(SHAPE/*.yaml)
dms_yamls=(DMS/*.yaml)
yamls=("${shape_yamls[@]}" "${dms_yamls[@]}")

if [ ${#yamls[@]} -eq 0 ]; then
  echo "No YAML files found under SHAPE/ or DMS/." >&2
  exit 1
fi

if [ -n "${dataset_filter}" ]; then
  filtered=()
  for yaml in "${yamls[@]}"; do
    if [ "$(basename "${yaml}" .yaml)" = "${dataset_filter}" ]; then
      filtered+=("${yaml}")
    fi
  done
  if [ ${#filtered[@]} -eq 0 ]; then
    echo "No YAML file found for dataset_id: ${dataset_filter}" >&2
    exit 1
  fi
  yamls=("${filtered[@]}")
fi

mkdir -p "${output_dir}"

for yaml in "${yamls[@]}"; do
  base="$(basename "${yaml}" .yaml)"
  output="${output_dir}/${base}.csv"

  echo "Validating ${yaml}"
  linkml-validate --schema "${schema}" "${yaml}"

  echo "Validating OBI ID for ${yaml}"
  python3 scripts/validate_obi_ids.py "${yaml}"

  # creating_ids.py writes nothing (and removes a stale CSV) when the dataset
  # comment starts with "failed QC" or "skip", so fetchngs never downloads it.
  echo "Generating ${output}"
  python3 scripts/creating_ids.py "${yaml}" "${output}"
done
