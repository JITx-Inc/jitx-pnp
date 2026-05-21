import logging
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from jitx_pnp.pnp import _parse_instances


def test_parse_synthetic_returns_expected_row_count(synthetic_xml):
    rows = _parse_instances(synthetic_xml)
    # 9 INSTs in BOARD, but two are skipped (missing DESIGNATOR, missing POSE)
    assert len(rows) == 7


def test_parse_synthetic_rows_are_natural_sorted(synthetic_xml):
    rows = _parse_instances(synthetic_xml)
    designators = [r["RefDes"] for r in rows]
    assert designators == ["C2", "C10", "D1", "J1", "L1", "R1", "U1"]


def test_parse_synthetic_joins_mpn_from_schematic(synthetic_xml):
    rows = {r["RefDes"]: r for r in _parse_instances(synthetic_xml)}
    assert rows["C2"]["PN"] == "CGA2B3X7R1H103M050BB"
    assert rows["C10"]["PN"] == "04023D105KAT2A"


def test_parse_synthetic_first_multi_unit_props_wins(synthetic_xml):
    rows = {r["RefDes"]: r for r in _parse_instances(synthetic_xml)}
    assert rows["U1"]["PN"] == "STM32F103C8T6"


def test_parse_synthetic_missing_mpn_is_empty_string(synthetic_xml):
    rows = {r["RefDes"]: r for r in _parse_instances(synthetic_xml)}
    assert rows["L1"]["PN"] == ""
    assert rows["D1"]["PN"] == ""


def test_parse_synthetic_sanitizes_csv_injection(synthetic_xml):
    rows = {r["RefDes"]: r for r in _parse_instances(synthetic_xml)}
    assert rows["R1"]["PN"] == "'=DANGEROUS"
    assert rows["J1"]["PN"] == "'+1234"


def test_parse_synthetic_truncates_package_dollar_suffix(synthetic_xml):
    rows = {r["RefDes"]: r for r in _parse_instances(synthetic_xml)}
    assert rows["R1"]["Package"] == "Pkg0805"


def test_parse_synthetic_normalizes_side(synthetic_xml):
    rows = {r["RefDes"]: r for r in _parse_instances(synthetic_xml)}
    assert rows["U1"]["Side"] == "Top"  # was "TOP"
    assert rows["R1"]["Side"] == "Bottom"
    assert rows["J1"]["Side"] == "Top"  # unknown side defaulted


def test_parse_synthetic_safe_float_falls_back_for_garbage(synthetic_xml):
    rows = {r["RefDes"]: r for r in _parse_instances(synthetic_xml)}
    assert rows["D1"]["X"] == "0.000"
    assert rows["D1"]["Y"] == "0.000"
    assert rows["D1"]["Rotation"] == "0.000"


def test_parse_synthetic_warns_for_skipped_instances(synthetic_xml, caplog):
    with caplog.at_level(logging.WARNING, logger="jitx_pnp.pnp"):
        _parse_instances(synthetic_xml)
    messages = [r.getMessage() for r in caplog.records]
    assert any("no DESIGNATOR" in m for m in messages)
    assert any("X1" in m and "no POSE" in m for m in messages)


def test_parse_raises_when_board_element_is_missing(tmp_path):
    bad_xml = tmp_path / "no_board.xml"
    bad_xml.write_text("<?xml version='1.0'?><PROJECT><SCHEMATIC/></PROJECT>")
    with pytest.raises(ValueError, match="No <BOARD> element"):
        _parse_instances(bad_xml)


def test_parse_xml_must_be_well_formed(tmp_path):
    bad_xml = tmp_path / "broken.xml"
    bad_xml.write_text("<PROJECT><BOARD></PROJECT>")
    with pytest.raises(ET.ParseError):
        _parse_instances(bad_xml)


def test_parse_warns_when_no_components_found(tmp_path, caplog):
    empty = tmp_path / "empty_board.xml"
    empty.write_text("<?xml version='1.0'?><PROJECT><BOARD></BOARD></PROJECT>")
    with caplog.at_level(logging.WARNING, logger="jitx_pnp.pnp"):
        rows = _parse_instances(empty)
    assert rows == []
    assert any("No component instances found" in r.getMessage() for r in caplog.records)


def test_parse_formats_pose_values_to_three_decimals(synthetic_xml):
    rows = {r["RefDes"]: r for r in _parse_instances(synthetic_xml)}
    assert rows["U1"]["X"] == "50.500"
    assert rows["U1"]["Y"] == "60.600"
    assert rows["U1"]["Rotation"] == "270.000"


def test_parse_accepts_path_or_str(synthetic_xml: Path):
    rows_from_path = _parse_instances(synthetic_xml)
    rows_from_str = _parse_instances(str(synthetic_xml))
    assert rows_from_path == rows_from_str
