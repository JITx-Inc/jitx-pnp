"""Export pick-and-place files from JITX designs.

The package splits in two: `format` renders placements as a table and
imports no jitx, and `extract` populates those records from a captured
`RuntimeDesign`. The `plugin` module registers the jitx export entry point,
so the usual way in is the CLI:

    jitx design export pnp --output pnp.csv my.boards.Widget

`pick_and_place` is the Python API. It exists alongside the plugin rather
than behind it because the plugin registry derives its command-line flags
from the signature of `export`, so everything reachable that way is a flat
scalar: a caller that wants to be told which files were written, or to hand
in an already-resolved convention, needs a door that is not the CLI's.

Coordinates are millimetres in the design's own frame, unshifted, which is
what the sibling exporters emit, so a placement file and a fab image of the
same board agree with each other.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

# absolute rather than relative: a `from .format import ...` here would
# bind `format` in this file, and `format` is also what the flag that
# selects a layout is called
from jitxlib.pnp.format import BottomRotation, Part, TableFormat

if TYPE_CHECKING:
    from jitx.run import RuntimeDesign

__all__ = ["BottomRotation", "Part", "TableFormat", "pick_and_place"]


def _output(output: Path | str | None, design_name: str, format: TableFormat) -> Path:
    """The file to write: the one given, or `<cwd>/<scrubbed name>-pnp.<ext>`.

    The default is named after the design, so exporting two boards into one
    directory does not have the second overwrite the first.
    """
    from jitxlib.pnp.format import legal_stem

    if output is not None:
        return Path(output).absolute()
    return Path.cwd() / f"{legal_stem(design_name)}-pnp{format.suffix}"


def pick_and_place(
    design: "RuntimeDesign",
    *,
    output: Path | str | None = None,
    format: str | TableFormat = TableFormat.CSV,
    split_sides: bool = False,
    bottom_rotation: str | BottomRotation = BottomRotation.NATIVE,
    include_unsoldered: bool = False,
    overwrite: bool = False,
) -> list[Path]:
    """Write the placements of a captured design.

    Args:
        design: a captured `RuntimeDesign`.
        output: the file to write. Without one the file is named after the
            design in the current directory.
        format: `csv`, `tsv`, or `txt` for fixed-width columns.
        split_sides: write `<stem>_top` and `<stem>_bottom` instead of one
            file, dropping the `Side` column that the names now carry.
        bottom_rotation: how to write a bottom-side angle. The default
            reports the design's own angle; see
            :py:mod:`jitxlib.pnp.format.rotation`.
        include_unsoldered: keep components marked as not soldered, which
            are left out by default.
        overwrite: replace files that are already there.

    Returns:
        The files written, in the order they were written.

    Raises:
        ExportError: a component to be placed has no reference designator or
            no placement.
        ValueError: the format or the convention is not one this exporter
            writes, or a file is already there and `overwrite` is not set.
    """
    from jitxlib.pnp.extract.components import build
    from jitxlib.pnp.format import write
    from jitxlib.pnp.format.rotation import resolve as resolve_rotation
    from jitxlib.pnp.format.write import resolve as resolve_format

    table = resolve_format(format)
    convention = resolve_rotation(bottom_rotation)
    parts = build(design, include_unsoldered=include_unsoldered)
    return write(
        parts,
        _output(output, design.name, table),
        format=table,
        split_sides=split_sides,
        bottom_rotation=convention,
        overwrite=overwrite,
    )
