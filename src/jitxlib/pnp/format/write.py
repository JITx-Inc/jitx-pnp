"""Rendering a set of placements, and putting it on disk.

Text is written with `newline=""` so the delimited formats keep the CRLF the
`csv` module produces rather than having the platform translate it; a
spreadsheet reading a CSV expects RFC 4180 line endings wherever it runs.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable, Sequence
from enum import StrEnum
from pathlib import Path

from .model import BOTTOM, FIELDS, HEADERS, SPLIT_FIELDS, TOP, Part
from .model import natural_sort_key, sanitize
from .rotation import DEFAULT, BottomRotation, rotation


class TableFormat(StrEnum):
    """How a table is laid out."""

    CSV = "csv"
    TSV = "tsv"
    TXT = "txt"
    """Fixed-width columns, for reading rather than for a machine."""

    @property
    def suffix(self) -> str:
        """The file extension this format is conventionally written with."""
        return f".{self.value}"


def resolve(value: str | TableFormat) -> TableFormat:
    """Resolve the `--format` flag.

    Raises:
        ValueError: the format is not one this exporter writes, listing the
            ones it does.
    """
    try:
        return TableFormat(value)
    except ValueError:
        supported = ", ".join(member.value for member in TableFormat)
        raise ValueError(
            f"Unknown format {value!r}; this exporter writes: {supported}"
        ) from None


def _row(part: Part, convention: BottomRotation) -> dict[str, str]:
    """One record as the strings a file carries."""
    return {
        "RefDes": sanitize(part.designator),
        "X": f"{part.x:.3f}",
        "Y": f"{part.y:.3f}",
        "Rotation": f"{rotation(part.rotation, part.side, convention):.3f}",
        "PN": sanitize(part.mpn),
        "Manufacturer": sanitize(part.manufacturer),
        "Value": sanitize(part.value),
        "Package": sanitize(part.package),
        "Side": part.side,
    }


def _delimited(rows: Sequence[dict[str, str]], fields: Sequence[str], sep: str) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter=sep, lineterminator="\r\n")
    writer.writerow(fields)
    for row in rows:
        writer.writerow([row[field] for field in fields])
    return buffer.getvalue()


def _fixed_width(rows: Sequence[dict[str, str]], fields: Sequence[str]) -> str:
    widths = {
        field: max(
            [len(HEADERS[field])] + [len(row[field]) for row in rows],
        )
        for field in fields
    }

    def line(values: dict[str, str]) -> str:
        return "  ".join(values[field].ljust(widths[field]) for field in fields)

    lines = [
        line({field: HEADERS[field] for field in fields}),
        "  ".join("-" * widths[field] for field in fields),
    ]
    lines.extend(line(row) for row in rows)
    return "\n".join(lines) + "\n"


def render(
    parts: Iterable[Part],
    *,
    fields: Sequence[str] = FIELDS,
    format: TableFormat = TableFormat.CSV,
    bottom_rotation: BottomRotation = DEFAULT,
) -> str:
    """Render placements as a table.

    Sorting is natural on the designator, so C2 precedes C10.

    Args:
        parts: the placements to render, in any order.
        fields: which columns to emit; the sequence order is the column
            order. Defaults to every column.
        bottom_rotation: how to write a bottom-side angle.
    """
    rows = [_row(part, bottom_rotation) for part in parts]
    rows.sort(key=lambda row: natural_sort_key(row["RefDes"]))
    if format is TableFormat.TXT:
        return _fixed_width(rows, fields)
    return _delimited(rows, fields, "\t" if format is TableFormat.TSV else ",")


def _guard(paths: Sequence[Path], overwrite: bool) -> None:
    """Refuse the whole set if any of it is already there.

    Checked up front rather than file by file: splitting writes two, and a
    refusal on the second one after the first was written leaves half an
    export behind.
    """
    if overwrite:
        return
    for path in paths:
        if path.exists():
            raise ValueError(
                f"Output path {path} already exists and overwrite was not specified"
            )


def _publish(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def write(
    parts: Iterable[Part],
    output: Path,
    *,
    format: TableFormat = TableFormat.CSV,
    split_sides: bool = False,
    bottom_rotation: BottomRotation = DEFAULT,
    overwrite: bool = False,
) -> list[Path]:
    """Write placements to `output`, or to one file per side beside it.

    Splitting writes `<stem>_top<suffix>` and `<stem>_bottom<suffix>` and not
    `output` itself, drops the `Side` column, which the name now carries, and
    skips a side with nothing on it rather than leaving an empty file for an
    operator to wonder about.

    Args:
        parts: the placements to write.
        output: the file to write, or the name the per-side files derive from.
        split_sides: write one file per populated side instead of one file.
        bottom_rotation: how to write a bottom-side angle.
        overwrite: replace files that are already there.

    Returns:
        The files written.

    Raises:
        ValueError: a file is already there and `overwrite` is not set. It is
            raised before anything is written, so a run either produces the
            whole set or leaves the previous one alone.
    """
    parts = list(parts)
    if not split_sides:
        _guard([output], overwrite)
        _publish(output, render(parts, format=format, bottom_rotation=bottom_rotation))
        return [output]

    populated: list[tuple[Path, list[Part]]] = []
    for side in (TOP, BOTTOM):
        on_side = [part for part in parts if part.side == side]
        if on_side:
            path = output.with_stem(f"{output.stem}_{side.lower()}")
            populated.append((path, on_side))

    _guard([path for path, _ in populated], overwrite)
    for path, on_side in populated:
        _publish(
            path,
            render(
                on_side,
                fields=SPLIT_FIELDS,
                format=format,
                bottom_rotation=bottom_rotation,
            ),
        )
    return [path for path, _ in populated]
