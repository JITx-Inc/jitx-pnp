import pytest

from jitx_pnp import pick_and_place


def test_returns_csv_string_with_header(synthetic_xml):
    result = pick_and_place(synthetic_xml)
    assert result.startswith("RefDes,X,Y,Rotation,PN,Package,Side")
    # Header + 7 components = 8 lines.
    assert len(result.strip().splitlines()) == 8


def test_writes_to_output_file(synthetic_xml, tmp_path):
    out = tmp_path / "pnp.csv"
    pick_and_place(synthetic_xml, output_file=out)
    assert out.exists()
    text = out.read_text()
    assert text.startswith("RefDes,X,Y,Rotation,PN,Package,Side")


def test_creates_parent_directories_for_output(synthetic_xml, tmp_path):
    nested = tmp_path / "deep" / "nested" / "out.csv"
    pick_and_place(synthetic_xml, output_file=nested)
    assert nested.exists()


def test_tsv_format_uses_tabs(synthetic_xml):
    result = pick_and_place(synthetic_xml, fmt="tsv")
    first_line = result.splitlines()[0]
    assert first_line == "RefDes\tX\tY\tRotation\tPN\tPackage\tSide"


def test_txt_format_produces_fixed_width(synthetic_xml):
    result = pick_and_place(synthetic_xml, fmt="txt")
    lines = result.splitlines()
    # Header + separator row + 7 components = 9 lines.
    assert len(lines) == 9
    assert set(lines[1].replace(" ", "")) == {"-"}


def test_split_sides_writes_top_and_bottom_files(synthetic_xml, tmp_path):
    out = tmp_path / "pnp.csv"
    pick_and_place(synthetic_xml, output_file=out, split_sides=True)
    top = tmp_path / "pnp_top.csv"
    bottom = tmp_path / "pnp_bottom.csv"
    assert top.exists()
    assert bottom.exists()
    # Combined (single-file) output not written when split_sides is True.
    assert not out.exists()


def test_split_sides_omits_side_column(synthetic_xml, tmp_path):
    out = tmp_path / "pnp.csv"
    pick_and_place(synthetic_xml, output_file=out, split_sides=True)
    top_text = (tmp_path / "pnp_top.csv").read_text()
    assert top_text.startswith("RefDes,X,Y,Rotation,PN,Package\n")
    assert ",Top" not in top_text


def test_split_sides_skips_empty_side(synthetic_xml, tmp_path):
    # synthetic.xml has Top components but only one Bottom (R1).
    # Construct a fixture with no Bottom components by reusing the fact that
    # split_sides should skip writing an empty side. We use a tmp XML.
    only_top = tmp_path / "top_only.xml"
    only_top.write_text(
        "<?xml version='1.0'?><PROJECT><BOARD>"
        '<INST DESIGNATOR="C1" SIDE="Top" PACKAGE="P">'
        '<POSE X="1" Y="2" ANGLE="0"/></INST>'
        "</BOARD></PROJECT>"
    )
    out = tmp_path / "pnp.csv"
    pick_and_place(only_top, output_file=out, split_sides=True)
    assert (tmp_path / "pnp_top.csv").exists()
    assert not (tmp_path / "pnp_bottom.csv").exists()


def test_raises_when_input_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        pick_and_place(tmp_path / "does_not_exist.xml")


def test_unknown_format_falls_back_to_csv(synthetic_xml):
    # The implementation treats anything other than "tsv"/"txt" as csv.
    # This locks that contract in.
    csv_out = pick_and_place(synthetic_xml, fmt="csv")
    fallback = pick_and_place(synthetic_xml, fmt="something-else")
    assert csv_out == fallback
