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
        return b'{"esearchresult": {"idlist": ["12345"]}}'


def test_candidate_taxonomy_names_formats_influenza_strain():
    assert validate_ncbi_taxonomy.candidate_taxonomy_names(
        "Influenza A virus",
        "A/Puerto Rico/8/1934(H1N1)",
    ) == ["Influenza A virus (A/Puerto Rico/8/1934(H1N1))"]


def test_candidate_taxonomy_names_formats_rotavirus_rf_strain():
    assert "Bovine rotavirus strain RF" in validate_ncbi_taxonomy.candidate_taxonomy_names(
        "Rotavirus A",
        "RF",
    )


def test_candidate_taxonomy_names_includes_ncbi_aliases():
    assert (
        "Severe acute respiratory syndrome coronavirus 2 isolate Wuhan-Hu-1"
        in validate_ncbi_taxonomy.candidate_taxonomy_names("SARS-CoV-2", "Wuhan-Hu-1")
    )


def test_taxonomy_names_to_try_adds_species_level_alias_for_sars_cov_2():
    assert "Severe acute respiratory syndrome coronavirus 2" in (
        validate_ncbi_taxonomy.taxonomy_names_to_try("SARS-CoV-2", "USA-WA1/2020")
    )


def test_taxonomy_names_to_try_adds_species_level_alias_for_hiv():
    names = validate_ncbi_taxonomy.taxonomy_names_to_try("HIV", "HIV-1_NL4-3")

    assert "Human immunodeficiency virus 1" in names
    assert "HIV" not in names


def test_taxonomy_names_to_try_adds_species_level_name_for_zika():
    assert "Zika virus" in (
        validate_ncbi_taxonomy.taxonomy_names_to_try("Zika virus", "KJ776791_HPF2013")
    )


def test_validate_metadata_file_passes_when_viral_strain_resolves(tmp_path):
    yaml_path = tmp_path / "rnastruct00014.yaml"
    yaml_path.write_text(
        (
            "dataset_id: rnastruct00014\n"
            "organism: Influenza A virus\n"
            "strain: A/Puerto Rico/8/1934(H1N1)\n"
            "raw_data:\n"
            "  repository: GEO\n"
            "  accession: GSE122286\n"
            "  run_accessions: []\n"
        ),
        encoding="utf-8",
    )

    def fake_search(name: str) -> list[str]:
        if name == "Influenza A virus (A/Puerto Rico/8/1934(H1N1))":
            return ["211044"]
        return []

    assert validate_ncbi_taxonomy.validate_metadata_file(yaml_path, search=fake_search) == []


def test_validate_metadata_file_accepts_sars_cov_2_species_level_taxon(tmp_path):
    yaml_path = tmp_path / "rnastruct00026.yaml"
    yaml_path.write_text(
        (
            "dataset_id: rnastruct00026\n"
            "organism: SARS-CoV-2\n"
            "strain: USA-WA1/2020\n"
        ),
        encoding="utf-8",
    )

    def fake_search(name: str) -> list[str]:
        if name == "Severe acute respiratory syndrome coronavirus 2":
            return ["2697049"]
        return []

    assert validate_ncbi_taxonomy.validate_metadata_file(yaml_path, search=fake_search) == []


def test_validate_metadata_file_requires_strain_for_viral_organism(tmp_path):
    yaml_path = tmp_path / "rnastruct00014.yaml"
    yaml_path.write_text(
        "dataset_id: rnastruct00014\norganism: Influenza A virus\n",
        encoding="utf-8",
    )

    issues = validate_ncbi_taxonomy.validate_metadata_file(yaml_path, search=lambda name: [])

    assert issues == [
        f"{yaml_path}: viral organism 'Influenza A virus' requires top-level strain"
    ]


def test_validate_metadata_file_reports_unresolved_strain(tmp_path):
    yaml_path = tmp_path / "rnastruct00014.yaml"
    yaml_path.write_text(
        (
            "dataset_id: rnastruct00014\n"
            "organism: Influenza A virus\n"
            "strain: Unknown\n"
        ),
        encoding="utf-8",
    )

    issues = validate_ncbi_taxonomy.validate_metadata_file(yaml_path, search=lambda name: [])

    assert len(issues) == 1
    assert "did not resolve to NCBI Taxonomy" in issues[0]


def test_search_ncbi_taxonomy_retries_rate_limit(monkeypatch):
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

    assert validate_ncbi_taxonomy.search_ncbi_taxonomy("Influenza A virus") == ["12345"]
    assert calls == 2


def test_validate_metadata_file_reports_ncbi_lookup_error(tmp_path):
    yaml_path = tmp_path / "rnastruct00014.yaml"
    yaml_path.write_text(
        (
            "dataset_id: rnastruct00014\n"
            "organism: Influenza A virus\n"
            "strain: A/Puerto Rico/8/1934(H1N1)\n"
        ),
        encoding="utf-8",
    )

    def fake_search(_name: str) -> list[str]:
        raise validate_ncbi_taxonomy.NcbiTaxonomyLookupError("rate limited")

    issues = validate_ncbi_taxonomy.validate_metadata_file(yaml_path, search=fake_search)

    assert len(issues) == 1
    assert "NCBI Taxonomy lookup failed" in issues[0]
    assert "rate limited" in issues[0]


def test_validate_metadata_files_caches_taxonomy_searches(tmp_path):
    first_path = tmp_path / "first.yaml"
    second_path = tmp_path / "second.yaml"
    content = (
        "dataset_id: rnastruct00014\n"
        "organism: Influenza A virus\n"
        "strain: A/Puerto Rico/8/1934(H1N1)\n"
    )
    first_path.write_text(content, encoding="utf-8")
    second_path.write_text(content, encoding="utf-8")
    calls: list[str] = []

    def fake_search(name: str) -> list[str]:
        calls.append(name)
        return ["211044"]

    issues = validate_ncbi_taxonomy.validate_metadata_files(
        [first_path, second_path],
        search=fake_search,
    )

    assert issues == []
    assert calls == ["Influenza A virus (A/Puerto Rico/8/1934(H1N1))"]
