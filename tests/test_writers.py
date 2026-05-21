from jitx_pnp.pnp import (
    ALL_FIELDS,
    FIXED_WIDTH_HEADERS,
    _write_delimited,
    _write_fixed_width,
)


def _sample_rows():
    return [
        {
            "RefDes": "C1",
            "X": "1.000",
            "Y": "2.000",
            "Rotation": "0.000",
            "PN": "PARTA",
            "Package": "Pkg0402",
            "Side": "Top",
        },
        {
            "RefDes": "R1",
            "X": "3.000",
            "Y": "4.000",
            "Rotation": "90.000",
            "PN": "PARTBLONG",
            "Package": "Pkg0805",
            "Side": "Bottom",
        },
    ]


def test_csv_writer_emits_header_and_rows():
    out = _write_delimited(_sample_rows(), ALL_FIELDS, delimiter=",")
    lines = out.splitlines()
    assert lines[0] == "RefDes,X,Y,Rotation,PN,Package,Side"
    assert lines[1] == "C1,1.000,2.000,0.000,PARTA,Pkg0402,Top"
    assert lines[2] == "R1,3.000,4.000,90.000,PARTBLONG,Pkg0805,Bottom"


def test_tsv_writer_uses_tab_delimiter():
    out = _write_delimited(_sample_rows(), ALL_FIELDS, delimiter="\t")
    assert "\t" in out.splitlines()[0]
    assert "," not in out.splitlines()[0]


def test_delimited_writer_respects_field_subset():
    fields = ["RefDes", "X", "Y"]
    out = _write_delimited(_sample_rows(), fields, delimiter=",")
    assert out.splitlines()[0] == "RefDes,X,Y"
    # extrasaction='ignore' means extra dict keys are dropped, not crashed
    assert "Package" not in out


def test_fixed_width_writer_aligns_columns_and_inserts_separator():
    out = _write_fixed_width(_sample_rows(), ALL_FIELDS, FIXED_WIDTH_HEADERS)
    lines = out.splitlines()
    # Header row, separator row, then one row per component.
    assert len(lines) == 4
    # Separator row is dashes joined with the same two-space separator.
    assert set(lines[1].replace(" ", "")) == {"-"}
    # PN column width is governed by the longest value ("PARTBLONG" = 9).
    assert "PARTBLONG" in lines[3]
    assert "PARTA    " in lines[2]  # "PARTA" padded to width 9


def test_fixed_width_uses_friendly_headers():
    out = _write_fixed_width(_sample_rows(), ALL_FIELDS, FIXED_WIDTH_HEADERS)
    header = out.splitlines()[0]
    assert "REF DES" in header
    assert "X COORD" in header
    assert "ROT" in header
