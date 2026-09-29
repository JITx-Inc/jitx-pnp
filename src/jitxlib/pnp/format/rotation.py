"""The bottom-side rotation conventions a placement file can be written in.

A top-side angle is the design's own angle under every convention. A
bottom-side one is not, and the three conventions in use across the JITX
exporters disagree: `jitxlib-jlcpcb` writes `-r`, Gerber X3's `.CRot` and
Siemens Xpedition write `r + 180`, and the design itself says `r`. They
coincide at exactly the angles that hide a mistake, so anything checking this
has to use an angle that is not a multiple of 90.
"""

from __future__ import annotations

from enum import StrEnum

from .model import BOTTOM


class BottomRotation(StrEnum):
    """How a bottom-side angle is written."""

    NATIVE = "native"
    """The design's own angle, unchanged. The `Side` column carries the rest."""

    NEGATE = "negate"
    """`-r`, as `jitxlib-jlcpcb` writes a JLCPCB CPL."""

    FLIP = "flip"
    """`r + 180`, as Gerber X3's `.CRot` and Xpedition's layout writer use."""


DEFAULT = BottomRotation.NATIVE
"""This library is fab-agnostic, so it reports what the design says.

A house that needs its own convention has a library of its own to put it in,
the way `jitxlib-jlcpcb` owns the JLCPCB rule.
"""


def resolve(value: str | BottomRotation) -> BottomRotation:
    """Resolve the `--bottom-rotation` flag.

    Raises:
        ValueError: the convention is not one this exporter writes, listing
            the ones it does.
    """
    try:
        return BottomRotation(value)
    except ValueError:
        supported = ", ".join(member.value for member in BottomRotation)
        raise ValueError(
            f"Unknown bottom rotation {value!r}; this exporter writes: {supported}"
        ) from None


def rotation(degrees: float, side: str, convention: BottomRotation) -> float:
    """The angle to write for a placement, in degrees.

    JITX composes a placement as `R(r) . diag(sx, sy)` and a bottom placement
    sets `sx = -1`, so a bottom part is `R(r) . diag(-1, 1)`.

    `negate` targets a frame mirrored about the other axis, `R(t) . diag(1,
    -1)`. Since `diag(-1, 1) = R(180) . diag(1, -1)`, that frame reads the
    same placement as `t = r + 180`, and it writes `180 - t`, which is `-r`.
    This is emphatically not `180 - r`: the two differ by 180 degrees at
    every angle.

    `flip` targets a frame whose bottom zero is the top zero flipped along X,
    which is `diag(1, -1)` again but written directly as `t`, so it writes
    `r + 180`.

    Args:
        degrees: the design's own angle, counter-clockwise, viewed from the top.
        side: `"Top"` or `"Bottom"`, as carried on a
            :py:class:`~jitxlib.pnp.format.model.Part`.
        convention: how to write a bottom-side angle.
    """
    if side != BOTTOM or convention is BottomRotation.NATIVE:
        return degrees % 360.0
    if convention is BottomRotation.NEGATE:
        return -degrees % 360.0
    return (degrees + 180.0) % 360.0
