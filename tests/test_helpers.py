import logging

from jitx_pnp.pnp import (
    _natural_sort_key,
    _normalize_side,
    _safe_float,
    _sanitize_csv_field,
)


def test_natural_sort_key_sorts_numeric_suffixes_correctly():
    items = ["C10", "C2", "C1", "R1", "C20"]
    assert sorted(items, key=_natural_sort_key) == ["C1", "C2", "C10", "C20", "R1"]


def test_natural_sort_key_handles_no_digits():
    assert _natural_sort_key("FOO") == ["FOO", ""] or _natural_sort_key("FOO") == ["FOO"]


def test_safe_float_parses_valid_numbers():
    assert _safe_float("3.14") == 3.14
    assert _safe_float("0") == 0.0
    assert _safe_float("-1.5") == -1.5


def test_safe_float_falls_back_on_garbage():
    assert _safe_float("abc") == 0.0
    assert _safe_float("") == 0.0
    assert _safe_float(None) == 0.0


def test_safe_float_uses_provided_default():
    assert _safe_float("nope", default=99.0) == 99.0
    assert _safe_float(None, default=-1.0) == -1.0


def test_sanitize_csv_field_escapes_formula_prefixes():
    for prefix in ("=", "+", "-", "@"):
        assert _sanitize_csv_field(f"{prefix}DANGEROUS") == f"'{prefix}DANGEROUS"


def test_sanitize_csv_field_passes_through_safe_values():
    assert _sanitize_csv_field("CGA2B3X7R1H103M050BB") == "CGA2B3X7R1H103M050BB"
    assert _sanitize_csv_field("") == ""
    assert _sanitize_csv_field("123-456") == "123-456"


def test_normalize_side_handles_canonical_values():
    assert _normalize_side("Top") == "Top"
    assert _normalize_side("Bottom") == "Bottom"


def test_normalize_side_is_case_insensitive():
    assert _normalize_side("TOP") == "Top"
    assert _normalize_side("bottom") == "Bottom"
    assert _normalize_side("  top  ") == "Top"


def test_normalize_side_defaults_unknown_to_top_with_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="jitx_pnp.pnp"):
        result = _normalize_side("Side1")
    assert result == "Top"
    assert any("Unrecognized board side" in r.getMessage() for r in caplog.records)
