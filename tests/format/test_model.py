"""Designator ordering, formula quoting, and filename stems."""

from __future__ import annotations

from jitxlib.pnp.format.model import legal_stem, natural_sort_key, sanitize


def test_designators_order_by_number_rather_than_by_text():
    names = ["C10", "C2", "R1", "C1"]
    assert sorted(names, key=natural_sort_key) == ["C1", "C2", "C10", "R1"]


def test_a_designator_with_no_digits_still_orders():
    assert sorted(["ANT", "C1"], key=natural_sort_key) == ["ANT", "C1"]


def test_a_field_opening_as_a_formula_is_quoted():
    for lead in ("=", "+", "-", "@"):
        assert sanitize(f"{lead}4.7K") == f"'{lead}4.7K"


def test_an_ordinary_field_is_untouched():
    assert sanitize("GRM155R60E475ME76D") == "GRM155R60E475ME76D"
    assert sanitize("") == ""


def test_a_module_path_becomes_one_stem_rather_than_a_suffix():
    assert legal_stem("demo.boards.Widget") == "demo_boards_Widget"


def test_a_stem_of_nothing_usable_still_names_a_file():
    assert legal_stem("...") == "design"
