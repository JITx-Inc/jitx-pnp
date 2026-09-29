"""The pick-and-place record and the shapes the writers render it in.

No jitx imports anywhere in this package: a row is plain strings and floats,
so every writer and the rotation rule are testable without a runtime.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

TOP = "Top"
BOTTOM = "Bottom"


@dataclass(frozen=True)
class Part:
    """One placed component, in the design's own frame.

    Coordinates are millimetres and `rotation` is the design's own
    counter-clockwise angle in degrees, viewed from the top, for both sides.
    The bottom-side convention a machine expects is applied by the writer, so
    a record always says what the design says.
    """

    designator: str
    x: float
    y: float
    rotation: float
    mpn: str
    manufacturer: str
    value: str
    package: str
    side: str


FIELDS = (
    "RefDes",
    "X",
    "Y",
    "Rotation",
    "PN",
    "Manufacturer",
    "Value",
    "Package",
    "Side",
)
"""Column order of a file covering both sides."""

SPLIT_FIELDS = FIELDS[:-1]
"""Column order of a per-side file, where `Side` is implicit in the name."""

HEADERS = {
    "RefDes": "REF DES",
    "X": "X COORD",
    "Y": "Y COORD",
    "Rotation": "ROT",
    "PN": "PN",
    "Manufacturer": "MANUFACTURER",
    "Value": "VALUE",
    "Package": "PACKAGE",
    "Side": "SIDE",
}
"""Fixed-width column headings, which spell out what the CSV abbreviates."""

_DIGITS = re.compile(r"(\d+)")

# Spreadsheets read a cell opening with one of these as a formula rather than
# as text, so a part number like "-4.7K" would evaluate on open.
_FORMULA_LEAD = ("=", "+", "-", "@")


def natural_sort_key(value: str) -> tuple[str | int, ...]:
    """Split a designator into text and integer runs, so C2 precedes C10."""
    return tuple(
        int(piece) if piece.isdigit() else piece for piece in _DIGITS.split(value)
    )


def sanitize(value: str) -> str:
    """Quote a field a spreadsheet would otherwise evaluate as a formula."""
    if value and value[0] in _FORMULA_LEAD:
        return "'" + value
    return value


def legal_stem(name: str) -> str:
    """A filename stem from a design's fully qualified name.

    Dots separate a module path rather than a suffix, so they become
    underscores instead of leaving a name whose extension is the class.
    """
    stem = "".join(
        character if character.isalnum() or character in "-_" else "_"
        for character in name
    ).strip("_")
    return stem or "design"
