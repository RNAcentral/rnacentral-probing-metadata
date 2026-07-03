from __future__ import annotations

import http.client
from io import BytesIO
import importlib.util
from pathlib import Path
from urllib.error import HTTPError


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "validate_ncbi_taxonomy.py"
    spec = importlib.util.spec_from_file_location("validate_ncbi_taxonomy", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_ncbi_taxonomy = _load_module()


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self) -> bytes:
        return b'{"result": {"9606": {"scientificname": "Homo sapiens"}}}'


def test_names_match_exact():
    assert validate_ncbi_taxonomy.names_match("Homo sapiens", "Homo sapiens")


def test_names_match_is_case_insensitive():
    assert validate_ncbi_taxonomy.names_match("homo sapiens", "Homo Sapiens")


def test_names_match_uses_alias_for_sars_cov_2():
    assert validate_ncbi_taxonomy.names_match(
        "SARS-CoV-2", "Severe acute respiratory syndrome coronavirus 2"
    )


def test_names_match_uses_alias_for_hiv():
    assert validate_ncbi_taxonomy.names_match("HIV", "Human immunodeficiency virus 1")


def test_names_match_rejects_mismatch():
    assert not validate_ncbi_taxonomy.names_match("Homo sapiens", "Mus musculus")


def test_names_match_accepts_strain_qualified_ncbi_name():
    assert validate_ncbi_taxonomy.names_match(
        "Parasynechococcus marenigrum", "Parasynechococcus marenigrum WH 8102"
    )


def test_names_match_rejects_different_species_with_shared_prefix():
    assert not validate_ncbi_taxonomy.names_match("Influenza A virus", "Influenza B virus")


def test_validate_metadata_file_passes_when_taxid_matches_organism(tmp_path):
    yaml_path = tmp_path / "rnastruct00001.yaml"
    yaml_path.write_text(
        (
            "dataset_id: rnastruct00001\n"
            "organism:\n"
            "  scientific_name: Homo sapiens\n"
            "  ncbi_taxid: 9606\n"
        ),
        encoding="utf-8",
    )

    def fake_fetch(taxid: str) -> str | None:
        return "Homo sapiens" if taxid == "9606" else None

    assert validate_ncbi_taxonomy.validate_metadata_file(yaml_path, fetch=fake_fetch) == []


def test_validate_metadata_file_accepts_sars_cov_2_alias(tmp_path):
    yaml_path = tmp_path / "rnastruct00026.yaml"
    yaml_path.write_text(
        (
            "dataset_id: rnastruct00026\n"
            "organism:\n"
            "  scientific_name: SARS-CoV-2\n"
            "  ncbi_taxid: 2697049\n"
            "  strain: USA-WA1/2020\n"
        ),
        encoding="utf-8",
    )

    def fake_fetch(taxid: str) -> str | None:
        if taxid == "2697049":
            return "Severe acute respiratory syndrome coronavirus 2"
        return None

    assert validate_ncbi_taxonomy.validate_metadata_file(yaml_path, fetch=fake_fetch) == []


def test_validate_metadata_file_requires_strain_for_viral_organism(tmp_path):
    yaml_path = tmp_path / "rnastruct00014.yaml"
    yaml_path.write_text(
        (
            "dataset_id: rnastruct00014\n"
            "organism:\n"
            "  scientific_name: Influenza A virus\n"
            "  ncbi_taxid: 11320\n"
        ),
        encoding="utf-8",
    )

    def fake_fetch(taxid: str) -> str | None:
        return "Influenza A virus" if taxid == "11320" else None

    issues = validate_ncbi_taxonomy.validate_metadata_file(yaml_path, fetch=fake_fetch)

    assert issues == [
        f"{yaml_path}: viral organism 'Influenza A virus' requires organism.strain"
    ]


def test_validate_metadata_file_reports_missing_taxid(tmp_path):
    yaml_path = tmp_path / "rnastruct00099.yaml"
    yaml_path.write_text(
        "dataset_id: rnastruct00099\norganism:\n  scientific_name: Homo sapiens\n",
        encoding="utf-8",
    )

    issues = validate_ncbi_taxonomy.validate_metadata_file(yaml_path, fetch=lambda taxid: None)

    assert issues == [
        f"{yaml_path}: organism.ncbi_taxid must be a plain integer, got ''"
    ]


def test_validate_metadata_file_reports_nonexistent_taxid(tmp_path):
    yaml_path = tmp_path / "rnastruct00099.yaml"
    yaml_path.write_text(
        (
            "dataset_id: rnastruct00099\n"
            "organism:\n"
            "  scientific_name: Homo sapiens\n"
            "  ncbi_taxid: 999999999\n"
        ),
        encoding="utf-8",
    )

    issues = validate_ncbi_taxonomy.validate_metadata_file(yaml_path, fetch=lambda taxid: None)

    assert issues == [
        f"{yaml_path}: ncbi_taxid '999999999' does not exist in NCBI Taxonomy"
    ]


def test_validate_metadata_file_reports_name_taxid_mismatch(tmp_path):
    yaml_path = tmp_path / "rnastruct00099.yaml"
    yaml_path.write_text(
        (
            "dataset_id: rnastruct00099\n"
            "organism:\n"
            "  scientific_name: Homo sapiens\n"
            "  ncbi_taxid: 10090\n"
        ),
        encoding="utf-8",
    )

    def fake_fetch(taxid: str) -> str | None:
        return "Mus musculus" if taxid == "10090" else None

    issues = validate_ncbi_taxonomy.validate_metadata_file(yaml_path, fetch=fake_fetch)

    assert issues == [
        f"{yaml_path}: organism 'Homo sapiens' does not match NCBI Taxonomy name "
        f"'Mus musculus' for ncbi_taxid '10090'"
    ]


def test_fetch_taxonomy_name_retries_rate_limit(monkeypatch):
    calls = 0

    def fake_urlopen(request, timeout=30):
        nonlocal calls
        assert timeout == 30
        calls += 1
        if calls == 1:
            raise HTTPError(
                request.full_url,
                429,
                "Too Many Requests",
                http.client.HTTPMessage(),
                BytesIO(b""),
            )
        return FakeResponse()

    monkeypatch.setattr(validate_ncbi_taxonomy, "urlopen", fake_urlopen)
    monkeypatch.setattr(validate_ncbi_taxonomy.time, "sleep", lambda _seconds: None)

    assert validate_ncbi_taxonomy.fetch_taxonomy_name("9606") == "Homo sapiens"
    assert calls == 2


def test_validate_metadata_file_reports_ncbi_lookup_error(tmp_path):
    yaml_path = tmp_path / "rnastruct00014.yaml"
    yaml_path.write_text(
        (
            "dataset_id: rnastruct00014\n"
            "organism:\n"
            "  scientific_name: Influenza A virus\n"
            "  ncbi_taxid: 11320\n"
            "  strain: A/Puerto Rico/8/1934(H1N1)\n"
        ),
        encoding="utf-8",
    )

    def fake_fetch(_taxid: str) -> str | None:
        raise validate_ncbi_taxonomy.NcbiTaxonomyLookupError("rate limited")

    issues = validate_ncbi_taxonomy.validate_metadata_file(yaml_path, fetch=fake_fetch)

    assert len(issues) == 1
    assert "NCBI Taxonomy lookup failed" in issues[0]
    assert "rate limited" in issues[0]


def test_validate_metadata_files_caches_taxonomy_lookups(tmp_path):
    first_path = tmp_path / "first.yaml"
    second_path = tmp_path / "second.yaml"
    content = (
        "dataset_id: rnastruct00014\n"
        "organism:\n"
        "  scientific_name: Influenza A virus\n"
        "  ncbi_taxid: 11320\n"
        "  strain: A/Puerto Rico/8/1934(H1N1)\n"
    )
    first_path.write_text(content, encoding="utf-8")
    second_path.write_text(content, encoding="utf-8")
    calls: list[str] = []

    def fake_fetch(taxid: str) -> str | None:
        calls.append(taxid)
        return "Influenza A virus"

    issues = validate_ncbi_taxonomy.validate_metadata_files(
        [first_path, second_path],
        fetch=fake_fetch,
    )

    assert issues == []
    assert calls == ["11320"]
