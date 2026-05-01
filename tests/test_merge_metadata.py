from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "merge_metadata.py"
    spec = importlib.util.spec_from_file_location("merge_metadata", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


merge_metadata = _load_module()
REPO_ROOT = Path(__file__).resolve().parents[1]
SHAPE_YAML = REPO_ROOT / "SHAPE" / "rnastruct00001.yaml"


def test_extract_run_metadata_map_includes_sample_fields():
    metadata = {
        "raw_data": {
            "run_accessions": [
                {
                    "accession": "GSM1",
                    "sample_name": "HeLa_treated_r1",
                    "cell_line": "HeLa",
                    "condition": "treated",
                    "replicate": 1,
                }
            ]
        }
    }

    result = merge_metadata.extract_run_metadata_map(metadata)

    assert result == {
        "GSM1": {
            "sample_name": "HeLa_treated_r1",
            "cell_line": "HeLa",
            "condition": "treated",
            "replicate": "1",
        }
    }


def test_extract_organism_name_keeps_non_viral_organism_unchanged():
    metadata = {"organism": "Homo sapiens", "strain": "not-used"}

    assert merge_metadata.extract_organism_name(metadata) == "Homo sapiens"


def test_extract_organism_name_adds_strain_for_viral_organism():
    metadata = {
        "organism": "Influenza A virus",
        "strain": "A/Puerto Rico/8/1934(H1N1)",
    }

    assert (
        merge_metadata.extract_organism_name(metadata)
        == "Influenza A virus (A/Puerto Rico/8/1934(H1N1))"
    )


def test_main_writes_new_sample_metadata_columns(tmp_path, monkeypatch, capsys):
    samplesheet_path = tmp_path / "fetchngs.csv"
    output_path = tmp_path / "merged.csv"

    samplesheet_path.write_text(
        (
            "sample_alias,fastq_1,fastq_2\n"
            "GSM4333255,s1_R1.fastq.gz,s1_R2.fastq.gz\n"
            "GSM4333259,s2_R1.fastq.gz,s2_R2.fastq.gz\n"
            "GSMX,sx_R1.fastq.gz,sx_R2.fastq.gz\n"
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "merge_metadata.py",
            "--samplesheet",
            str(samplesheet_path),
            "--metadata",
            str(SHAPE_YAML),
            "--out",
            str(output_path),
        ],
    )

    rc = merge_metadata.main()
    assert rc == 0

    header = output_path.read_text(encoding="utf-8").splitlines()[0]
    assert header == (
        "sample,sample_id,fastq_1,fastq_2,method,principle,"
        "cell_line,condition,replicate,organism,pH,adapter_3p,adapter_5p,umi_pattern"
    )

    with output_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 2
    assert rows[0]["sample"] == "HEK293T_untreated_r1"
    assert rows[0]["cell_line"] == "HEK293T"
    assert rows[0]["condition"] == "untreated"
    assert rows[0]["replicate"] == "1"
    assert rows[0]["organism"] == "Homo sapiens"
    assert rows[1]["sample"] == "K562_untreated_r1"
    assert rows[1]["cell_line"] == "K562"
    assert rows[1]["condition"] == "untreated"
    assert rows[1]["replicate"] == "1"
    assert rows[1]["method"] == "SHAPE"

    out = capsys.readouterr().out
    assert f"Wrote 2 rows to {output_path}" in out


def test_main_writes_viral_organism_with_strain(tmp_path, monkeypatch):
    samplesheet_path = tmp_path / "fetchngs.csv"
    metadata_path = tmp_path / "metadata.yaml"
    output_path = tmp_path / "merged.csv"

    samplesheet_path.write_text(
        "sample_alias,fastq_1,fastq_2\nGSM3463235,s1_R1.fastq.gz,s1_R2.fastq.gz\n",
        encoding="utf-8",
    )
    metadata_path.write_text(
        (
            "dataset_id: rnastruct00014\n"
            "organism: Influenza A virus\n"
            "strain: A/Puerto Rico/8/1934(H1N1)\n"
            "experiment:\n"
            "  chemical: DMS\n"
            "  principle: MaP\n"
            "raw_data:\n"
            "  run_accessions:\n"
            "  - accession: GSM3463235\n"
            "    sample_name: PR8_treated\n"
            "    cell_line: IAV_PR8_in_vivo\n"
            "    condition: treated\n"
            "    replicate: 1\n"
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "merge_metadata.py",
            "--samplesheet",
            str(samplesheet_path),
            "--metadata",
            str(metadata_path),
            "--out",
            str(output_path),
        ],
    )

    rc = merge_metadata.main()
    assert rc == 0

    with output_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert rows[0]["organism"] == "Influenza A virus (A/Puerto Rico/8/1934(H1N1))"


def test_main_matches_experiment_accession_when_sample_alias_is_descriptive(
    tmp_path, monkeypatch
):
    samplesheet_path = tmp_path / "fetchngs.csv"
    metadata_path = tmp_path / "metadata.yaml"
    output_path = tmp_path / "merged.csv"

    samplesheet_path.write_text(
        (
            "sample_alias,experiment_accession,fastq_1,fastq_2\n"
            "PR8_SHAPE_MaP_1M7,SRX4223900,s1_R1.fastq.gz,s1_R2.fastq.gz\n"
            "PR8_SHAPE_MaP_DMSO,SRX4223899,s2_R1.fastq.gz,s2_R2.fastq.gz\n"
        ),
        encoding="utf-8",
    )
    metadata_path.write_text(
        (
            "dataset_id: rnastruct00015\n"
            "organism: Influenza A virus\n"
            "strain: A/Puerto Rico/8/1934(H1N1)\n"
            "experiment:\n"
            "  chemical: 1M7\n"
            "  principle: MaP\n"
            "raw_data:\n"
            "  run_accessions:\n"
            "  - accession: SRX4223900\n"
            "    sample_name: PR8_in_virio_treated\n"
            "    cell_line: IAV_PR8\n"
            "    condition: treated\n"
            "    replicate: 1\n"
            "  - accession: SRX4223899\n"
            "    sample_name: PR8_in_virio_untreated\n"
            "    cell_line: IAV_PR8\n"
            "    condition: untreated\n"
            "    replicate: 1\n"
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "merge_metadata.py",
            "--samplesheet",
            str(samplesheet_path),
            "--metadata",
            str(metadata_path),
            "--out",
            str(output_path),
        ],
    )

    rc = merge_metadata.main()
    assert rc == 0

    with output_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert [row["sample_id"] for row in rows] == ["SRX4223900", "SRX4223899"]
    assert [row["sample"] for row in rows] == [
        "PR8_in_virio_treated",
        "PR8_in_virio_untreated",
    ]
