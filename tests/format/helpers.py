"""A record factory for the format-layer tests. No jitx import anywhere."""

from __future__ import annotations

from jitxlib.pnp.format import TOP, Part


def part(
    designator: str,
    *,
    x: float = 0.0,
    y: float = 0.0,
    rotation: float = 0.0,
    mpn: str = "",
    manufacturer: str = "",
    value: str = "",
    package: str = "Land",
    side: str = TOP,
) -> Part:
    # A placement with everything but the designator defaulted, so a test
    # states only the fields it is about.
    return Part(
        designator=designator,
        x=x,
        y=y,
        rotation=rotation,
        mpn=mpn,
        manufacturer=manufacturer,
        value=value,
        package=package,
        side=side,
    )
