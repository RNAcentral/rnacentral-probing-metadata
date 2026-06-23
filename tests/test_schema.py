from __future__ import annotations

import re
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_YAML = REPO_ROOT / "schema" / "rnastruct.schema.yaml"
CURRENT_SCHEMA_VERSION = "1.0.0"


def metadata_files() -> list[Path]:
    return sorted((REPO_ROOT / "SHAPE").glob("*.yaml")) + sorted(
        (REPO_ROOT / "DMS").glob("*.yaml")
    )


def organism_pattern() -> re.Pattern[str]:
    with SCHEMA_YAML.open(encoding="utf-8") as handle:
        schema = yaml.safe_load(handle)
    pattern = schema["classes"]["Dataset"]["attributes"]["organism"]["pattern"]
    return re.compile(pattern)


def test_organism_pattern_accepts_latin_names_and_curated_viral_names():
    pattern = organism_pattern()

    assert pattern.fullmatch("Homo sapiens")
    assert pattern.fullmatch("Mus musculus castaneus")
    assert pattern.fullmatch("Influenza A virus")
    assert pattern.fullmatch("SARS-CoV-2")
    assert pattern.fullmatch("Zika virus")
    assert pattern.fullmatch("HIV")
    assert pattern.fullmatch("Rotavirus A")


def test_organism_pattern_rejects_unstructured_names():
    pattern = organism_pattern()

    assert pattern.fullmatch("not a species") is None
    assert pattern.fullmatch("Influenza") is None


def test_schema_declares_current_version():
    with SCHEMA_YAML.open(encoding="utf-8") as handle:
        schema = yaml.safe_load(handle)

    assert schema["version"] == CURRENT_SCHEMA_VERSION
    values = schema["enums"]["SchemaVersionEnum"]["permissible_values"]
    assert list(values) == [CURRENT_SCHEMA_VERSION]


def test_schema_allows_dataset_and_sample_comments():
    with SCHEMA_YAML.open(encoding="utf-8") as handle:
        schema = yaml.safe_load(handle)

    dataset_comment = schema["classes"]["Dataset"]["attributes"]["comment"]
    sample_comment = schema["classes"]["RunAccessionName"]["attributes"]["comment"]
    assert dataset_comment["range"] == "string"
    assert sample_comment["range"] == "string"


def test_metadata_files_declare_current_schema_version():
    paths = metadata_files()
    assert paths

    for path in paths:
        with path.open(encoding="utf-8") as handle:
            metadata = yaml.safe_load(handle)

        assert metadata["schema_version"] == CURRENT_SCHEMA_VERSION, path
