"""Tests for the skill taxonomy registry (no network, stdlib only)."""

from backend.skill_taxonomy import (
    validate_skill_taxonomy,
    get_ocr_table,
    get_llm_table,
    get_ws_table,
    get_anti_pattern_table,
    get_slo_table,
    get_workflow_table,
    _all_tables,
)


def test_taxonomy_valid():
    result = validate_skill_taxonomy()
    assert result["valid"] is True, result["errors"]


def test_ocr_table_nonempty():
    assert len(get_ocr_table().rows) >= 1


def test_no_duplicate_ids():
    ids = [row.id for table in _all_tables() for row in table.rows]
    assert len(ids) == len(set(ids)), "taxonomy IDs are not globally unique"


def test_all_six_tables_have_rows():
    for getter in (
        get_ocr_table,
        get_llm_table,
        get_ws_table,
        get_anti_pattern_table,
        get_slo_table,
        get_workflow_table,
    ):
        assert len(getter().rows) >= 1


def test_to_markdown_contains_rows():
    md = get_ocr_table().to_markdown()
    assert "backend_none" in md
    assert "| id | keywords | code_path |" in md
