import csv
import io
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path

log = logging.getLogger(__name__)

_NATURAL_SORT_RE = re.compile(r"(\d+)")


def _natural_sort_key(value: str) -> list[str | int]:
    """Split a string into text and integer parts for natural sorting.

    "C2" -> ["C", 2], "C10" -> ["C", 10], so C2 sorts before C10.
    """
    parts: list[str | int] = []
    for piece in _NATURAL_SORT_RE.split(value):
        if piece.isdigit():
            parts.append(int(piece))
        else:
            parts.append(piece)
    return parts


def _safe_float(value: str | None, default: float = 0.0) -> float:
    """Convert a string to float, returning default on failure."""
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _sanitize_csv_field(value: str) -> str:
    """Prevent CSV injection by escaping leading formula characters.

    Spreadsheet tools interpret cells starting with =, +, -, or @
    as formulas. Prefix with a single quote to force text interpretation.
    """
    if value and value[0] in ("=", "+", "-", "@"):
        return "'" + value
    return value


def _normalize_side(side: str) -> str:
    """Normalize board side values to 'Top' or 'Bottom'."""
    lower = side.strip().lower()
    if lower == "top":
        return "Top"
    elif lower == "bottom":
        return "Bottom"
    else:
        log.warning("Unrecognized board side '%s', defaulting to 'Top'", side)
        return "Top"


def _parse_instances(xml_path: Path) -> list[dict[str, str]]:
    """Parse component placement data from a JITX XML board export.

    Extracts position data from BOARD/INST elements and part number data
    from SCHEMATIC/SHEET/SCH-INST/PROPS elements, joining on designator.

    Returns a sorted list of row dicts with keys:
        RefDes, X, Y, Rotation, PN, Package, Side
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    board = root.find("BOARD")
    if board is None:
        raise ValueError(f"No <BOARD> element found in {xml_path}")

    # Build a designator -> MPN map from schematic data.
    # Only store the first occurrence per designator (multi-unit components
    # may have multiple SCH-INST entries sharing the same designator).
    props_map: dict[str, str] = {}
    for sch_inst in root.iter("SCH-INST"):
        props = sch_inst.find("PROPS")
        if props is not None:
            desig = props.get("DESIGNATOR")
            if desig and desig not in props_map:
                props_map[desig] = props.get("MPN", "")

    rows: list[dict[str, str]] = []
    for inst in board.findall("INST"):
        designator = inst.get("DESIGNATOR")
        if designator is None:
            log.warning("Skipping INST with no DESIGNATOR attribute")
            continue

        side = _normalize_side(inst.get("SIDE", "Top"))
        package = inst.get("PACKAGE", "")

        pose = inst.find("POSE")
        if pose is None:
            log.warning("Skipping %s: no POSE element", designator)
            continue

        x = _safe_float(pose.get("X"))
        y = _safe_float(pose.get("Y"))
        angle = _safe_float(pose.get("ANGLE"))

        rows.append(
            {
                "RefDes": designator,
                "X": f"{x:.3f}",
                "Y": f"{y:.3f}",
                "Rotation": f"{angle:.3f}",
                "PN": _sanitize_csv_field(props_map.get(designator, "")),
                "Package": _sanitize_csv_field(package.split("$")[0]),
                "Side": side,
            }
        )

    if not rows:
        log.warning("No component instances found in %s", xml_path)

    rows.sort(key=lambda r: _natural_sort_key(r["RefDes"]))
    return rows


def _write_delimited(
    rows: list[dict[str, str]],
    fieldnames: list[str],
    delimiter: str = ",",
) -> str:
    """Format rows as a delimited string (CSV or TSV)."""
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=fieldnames,
        extrasaction="ignore",
        delimiter=delimiter,
    )
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def _write_fixed_width(
    rows: list[dict[str, str]],
    fieldnames: list[str],
    headers: dict[str, str],
) -> str:
    """Format rows as a fixed-width text table."""
    # Compute column widths from headers and data.
    widths: dict[str, int] = {}
    for f in fieldnames:
        col_max = len(headers.get(f, f))
        for r in rows:
            col_max = max(col_max, len(r.get(f, "")))
        widths[f] = col_max

    def fmt_row(values: dict[str, str]) -> str:
        parts = [values.get(f, "").ljust(widths[f]) for f in fieldnames]
        return "  ".join(parts)

    header_row = fmt_row(headers)
    sep_row = "  ".join("-" * widths[f] for f in fieldnames)

    lines = [header_row, sep_row]
    for r in rows:
        lines.append(fmt_row(r))
    return "\n".join(lines) + "\n"


ALL_FIELDS = ["RefDes", "X", "Y", "Rotation", "PN", "Package", "Side"]
PER_SIDE_FIELDS = ["RefDes", "X", "Y", "Rotation", "PN", "Package"]

FIXED_WIDTH_HEADERS = {
    "RefDes": "REF DES",
    "X": "X COORD",
    "Y": "Y COORD",
    "Rotation": "ROT",
    "PN": "PN",
    "Package": "PACKAGE",
    "Side": "SIDE",
}


def pick_and_place(
    xml_file: str | Path,
    output_file: str | Path | None = None,
    split_sides: bool = False,
    fmt: str = "csv",
) -> str:
    """Generate a pick-and-place file from a JITX XML board export.

    Parses INST elements from the XML to extract component placement
    data (designator, position, rotation, part number, package, side).

    Args:
        xml_file: Path to the JITX XML board export file.
        output_file: Path to write the output file. If None, results are
            only returned as a string.
        split_sides: When True and output_file is set, write separate files
            per board side (<stem>_top.<ext>, <stem>_bottom.<ext>) with the
            Side column omitted. When False, write a single file.
        fmt: Output format — "csv", "tsv", or "txt" (fixed-width columns).

    Returns:
        Formatted string with all components (both sides, Side column included).
    """
    xml_path = Path(xml_file)
    if not xml_path.exists():
        raise FileNotFoundError(f"XML file not found: {xml_path}")

    rows = _parse_instances(xml_path)

    def writer(rows: list[dict[str, str]], fields: list[str]) -> str:
        if fmt == "txt":
            return _write_fixed_width(rows, fields, FIXED_WIDTH_HEADERS)
        elif fmt == "tsv":
            return _write_delimited(rows, fields, delimiter="\t")
        else:
            return _write_delimited(rows, fields)

    result = writer(rows, ALL_FIELDS)

    if output_file is not None:
        out = Path(output_file)
        out.parent.mkdir(parents=True, exist_ok=True)

        if split_sides:
            for side_label in ("Top", "Bottom"):
                side_rows = [r for r in rows if r["Side"] == side_label]
                if not side_rows:
                    continue
                tag = side_label.lower()
                side_path = out.with_stem(f"{out.stem}_{tag}")
                side_path.write_text(writer(side_rows, PER_SIDE_FIELDS))
        else:
            out.write_text(result)

    return result
