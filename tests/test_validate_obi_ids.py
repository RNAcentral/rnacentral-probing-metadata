from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "validate_obi_ids.py"
    spec = importlib.util.spec_from_file_location("validate_obi_ids", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_obi_ids = _load_module()


def _write_yaml(path: Path, chemical: str, obi: str | None) -> None:
    obi_line = "" if obi is None else f"  obi: {obi}\n"
    path.write_text(
        (
            "dataset_id: rnastruct99999\n"
            "organism: Homo sapiens\n"
            "experiment:\n"
            "  method: SHAPE-MaP\n"
            "  principle: MaP\n"
            f"{obi_line}"
            f"  chemical: {chemical}\n"
            "publication:\n"
            "  doi: 10.1000/test\n"
            "raw_data:\n"
            "  repository: GEO\n"
            "  accession: GSE123456\n"
            "  run_accessions:\n"
            "    - accession: GSM1001\n"
            "      sample_name: sample_1\n"
            "      cell_line: HeLa\n"
            "      condition: treated\n"
            "      replicate: 1\n"
        ),
        encoding="utf-8",
    )


def test_validate_metadata_file_accepts_expected_obi_pairs(tmp_path):
    for chemical, obi in validate_obi_ids.EXPECTED_OBI_BY_CHEMICAL.items():
        yaml_path = tmp_path / f"{chemical.replace(':', '_')}.yaml"
        _write_yaml(yaml_path, chemical, obi)

        assert validate_obi_ids.validate_metadata_file(yaml_path) == []


def test_validate_metadata_file_reports_mismatched_obi(tmp_path):
    yaml_path = tmp_path / "metadata.yaml"
    _write_yaml(yaml_path, "DMS", "OBI:0003886")

    issues = validate_obi_ids.validate_metadata_file(yaml_path)

    assert len(issues) == 1
    assert "chemical 'DMS' expects experiment.obi 'OBI:0001015'" in issues[0]
    assert "found 'OBI:0003886'" in issues[0]


def test_validate_metadata_file_reports_missing_obi(tmp_path):
    yaml_path = tmp_path / "metadata.yaml"
    _write_yaml(yaml_path, "NAI", None)

    issues = validate_obi_ids.validate_metadata_file(yaml_path)

    assert issues == [
        f"{yaml_path}: chemical 'NAI' requires experiment.obi 'OBI:0003886'"
    ]


def test_validate_metadata_file_reports_null_obi_as_missing(tmp_path):
    yaml_path = tmp_path / "metadata.yaml"
    _write_yaml(yaml_path, "NAI", "null")

    issues = validate_obi_ids.validate_metadata_file(yaml_path)

    assert issues == [
        f"{yaml_path}: chemical 'NAI' requires experiment.obi 'OBI:0003886'"
    ]


def test_validate_metadata_file_reports_unmapped_chemical(tmp_path):
    yaml_path = tmp_path / "metadata.yaml"
    _write_yaml(yaml_path, "UNKNOWN_REAGENT", "OBI:1234567")

    issues = validate_obi_ids.validate_metadata_file(yaml_path)

    assert issues == [f"{yaml_path}: no OBI mapping configured for chemical 'UNKNOWN_REAGENT'"]
