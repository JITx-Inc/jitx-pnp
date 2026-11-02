"""Rendering a table, and putting it on disk."""

from __future__ import annotations

import pytest

from jitxlib.pnp.format import BOTTOM, SPLIT_FIELDS, TOP
from jitxlib.pnp.format.rotation import BottomRotation
from jitxlib.pnp.format.write import TableFormat, render, resolve, write

from .helpers import part


def test_csv_leads_with_the_column_names():
    text = render([part("C1")])
    header, _ = text.split("\r\n", 1)
    assert header == "RefDes,X,Y,Rotation,PN,Manufacturer,Value,Package,Side"


def test_a_row_carries_three_decimals_and_the_side():
    text = render(
        [
            part(
                "C1",
                x=-5.175,
                y=4.12,
                rotation=270.0,
                mpn="04025A150FAT2A",
                manufacturer="AVX",
                value="15 pF",
                package="Chip0402",
            )
        ]
    )
    assert text.splitlines()[1] == (
        "C1,-5.175,4.120,270.000,04025A150FAT2A,AVX,15 pF,Chip0402,Top"
    )


def test_delimited_output_ends_its_lines_the_way_a_spreadsheet_expects():
    text = render([part("C1")])
    assert text.endswith("\r\n")
    assert "\r\r\n" not in text


def test_rows_are_ordered_naturally_by_designator():
    text = render([part("C10"), part("C2"), part("C1")])
    assert [line.split(",")[0] for line in text.splitlines()[1:]] == [
        "C1",
        "C2",
        "C10",
    ]


def test_tsv_separates_with_tabs():
    text = render([part("C1")], format=TableFormat.TSV)
    assert text.splitlines()[0].split("\t")[0] == "RefDes"
    assert "," not in text.splitlines()[1]


def test_fixed_width_pads_each_column_to_its_widest_value():
    text = render(
        [part("C1", package="Chip0402"), part("C10", package="QFN32")],
        format=TableFormat.TXT,
    )
    heading, rule, first, second = text.splitlines()
    assert heading.startswith("REF DES")
    assert set(rule) == {"-", " "}
    assert len(heading) == len(rule) == len(first) == len(second)
    assert text.endswith("\n") and not text.endswith("\n\n")


def test_fixed_width_names_the_new_columns_in_full():
    text = render([part("C1")], format=TableFormat.TXT)
    assert "MANUFACTURER" in text.splitlines()[0]
    assert "VALUE" in text.splitlines()[0]


def test_a_requested_subset_of_columns_is_the_whole_row():
    text = render([part("C1")], fields=SPLIT_FIELDS)
    assert text.splitlines()[0].endswith("Package")
    assert "Side" not in text.splitlines()[0]


def test_the_bottom_convention_reaches_the_rendered_row():
    parts = [part("C1", rotation=45.0, side=BOTTOM)]
    assert "315.000" in render(parts, bottom_rotation=BottomRotation.NEGATE)
    assert "225.000" in render(parts, bottom_rotation=BottomRotation.FLIP)
    assert "45.000" in render(parts)


def test_writing_leaves_the_bytes_the_renderer_produced(tmp_path):
    out = tmp_path / "nested" / "pnp.csv"
    assert write([part("C1")], out) == [out]
    assert out.read_bytes().count(b"\r\n") == 2


def test_splitting_names_a_file_per_populated_side(tmp_path):
    out = tmp_path / "pnp.csv"
    written = write([part("C1"), part("R1", side=BOTTOM)], out, split_sides=True)
    assert written == [tmp_path / "pnp_top.csv", tmp_path / "pnp_bottom.csv"]
    assert not out.exists()


def test_a_split_file_drops_the_column_its_name_carries(tmp_path):
    out = tmp_path / "pnp.csv"
    write([part("C1")], out, split_sides=True)
    # bytes, then decode: `Path.read_text` only grew `newline=` in 3.13, and
    # the point of the file is that nothing translated its line endings
    text = (tmp_path / "pnp_top.csv").read_bytes().decode()
    assert "Side" not in text.splitlines()[0]
    assert TOP not in text


def test_an_empty_side_leaves_no_file_to_wonder_about(tmp_path):
    out = tmp_path / "pnp.csv"
    written = write([part("C1")], out, split_sides=True)
    assert written == [tmp_path / "pnp_top.csv"]
    assert not (tmp_path / "pnp_bottom.csv").exists()


def test_an_existing_file_is_kept_unless_replacing_it_was_asked_for(tmp_path):
    out = tmp_path / "pnp.csv"
    out.write_text("keep me")
    with pytest.raises(ValueError, match="already exists"):
        write([part("C1")], out)
    assert out.read_text() == "keep me"
    write([part("C1")], out, overwrite=True)
    assert "RefDes" in out.read_text()


# `--output pnp.csv --format txt` is fixed-width text in `pnp.csv`. The suffix
# is what the caller asked for, and renaming it under them to match the layout
# would write a file they did not name.
def test_the_extension_comes_from_the_path_not_from_the_format(tmp_path):
    out = tmp_path / "pnp.csv"
    write([part("C1")], out, format=TableFormat.TXT)
    assert out.read_text().startswith("REF DES")


# The guard runs over the whole set before any of it is written. Top sorts
# first, so a conflict on the bottom file is the case where a file-by-file
# check would already have written the top one.
def test_a_refused_split_leaves_no_half_an_export_behind(tmp_path):
    out = tmp_path / "pnp.csv"
    (tmp_path / "pnp_bottom.csv").write_text("keep me")
    with pytest.raises(ValueError, match="already exists"):
        write([part("C1"), part("R1", side=BOTTOM)], out, split_sides=True)
    assert not (tmp_path / "pnp_top.csv").exists()
    assert (tmp_path / "pnp_bottom.csv").read_text() == "keep me"


def test_an_unknown_format_names_the_ones_that_exist():
    with pytest.raises(ValueError, match="csv, tsv, txt"):
        resolve("xlsx")
