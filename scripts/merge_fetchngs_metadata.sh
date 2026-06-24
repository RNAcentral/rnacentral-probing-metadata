#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <repo_dir> <outdir>" >&2
  exit 1
fi

repo_dir="$1"
outdir="$2"

merged_dir="${outdir}/samplesheet"
mkdir -p "${merged_dir}"

merged_outputs=()
skipped_count=0

shopt -s nullglob
for yaml in "${repo_dir}"/SHAPE/*.yaml "${repo_dir}"/DMS/*.yaml; do
  [ -s "${yaml}" ] || continue

  dataset_id="$(basename "${yaml}" .yaml)"
  samplesheet_csv="${outdir}/${dataset_id}/samplesheet/samplesheet.csv"

  if [ ! -s "${samplesheet_csv}" ]; then
    alt_match="$(find "${outdir}" -type f -name samplesheet.csv | grep "/${dataset_id}/" | head -n 1 || true)"
    if [ -n "${alt_match}" ]; then
      samplesheet_csv="${alt_match}"
    else
      echo "WARNING: samplesheet.csv not found for ${dataset_id}; skipping. Expected ${samplesheet_csv}" >&2
      skipped_count=$((skipped_count + 1))
      continue
    fi
  fi

  out_csv="${merged_dir}/${dataset_id}_samplesheet.csv"

  python3 "${repo_dir}/scripts/merge_metadata.py" \
    --samplesheet "${samplesheet_csv}" \
    --metadata "${yaml}" \
    --out "${out_csv}"

  if [ -s "${out_csv}" ]; then
    merged_outputs+=("${out_csv}")
  else
    skipped_count=$((skipped_count + 1))
  fi
done

manifest="${merged_dir}/rnastruct_samplesheets_manifest.txt"

if [ ${#merged_outputs[@]} -eq 0 ]; then
  : > "${manifest}"
  echo "ERROR: no merged rnastruct samplesheets were generated in ${merged_dir}" >&2
  exit 1
fi

printf "%s\n" "${merged_outputs[@]}" | sort > "${manifest}"

if [ "${skipped_count}" -gt 0 ]; then
  echo "WARNING: skipped ${skipped_count} dataset(s) without fetchngs samplesheets." >&2
fi
