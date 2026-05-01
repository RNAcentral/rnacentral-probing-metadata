from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MERGE_SCRIPT = REPO_ROOT / "scripts" / "merge_fetchngs_metadata.sh"


def test_merge_fetchngs_metadata_skips_missing_samplesheets(tmp_path):
    outdir = tmp_path / "FASTQ"
    fetchngs_samplesheet = outdir / "rnastruct00001" / "samplesheet" / "samplesheet.csv"
    merged_dir = outdir / "samplesheet"
    stale_merged = merged_dir / "rnastruct00003_samplesheet.csv"

    fetchngs_samplesheet.parent.mkdir(parents=True)
    fetchngs_samplesheet.write_text(
        "sample_alias,fastq_1,fastq_2\n"
        "GSM4333255,s1_R1.fastq.gz,s1_R2.fastq.gz\n",
        encoding="utf-8",
    )
    merged_dir.mkdir(parents=True)
    stale_merged.write_text("stale\n", encoding="utf-8")

    result = subprocess.run(
        [str(MERGE_SCRIPT), str(REPO_ROOT), str(outdir)],
        check=True,
        capture_output=True,
        text=True,
    )

    merged = merged_dir / "rnastruct00001_samplesheet.csv"
    manifest = merged_dir / "rnastruct_samplesheets_manifest.txt"

    assert merged.exists()
    assert manifest.read_text(encoding="utf-8").splitlines() == [str(merged)]
    assert "WARNING: samplesheet.csv not found for rnastruct00003; skipping." in result.stderr
    assert "WARNING: skipped " in result.stderr


def test_merge_fetchngs_metadata_fails_when_no_samplesheets_exist(tmp_path):
    outdir = tmp_path / "FASTQ"

    result = subprocess.run(
        [str(MERGE_SCRIPT), str(REPO_ROOT), str(outdir)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "ERROR: no merged rnastruct samplesheets were generated" in result.stderr
