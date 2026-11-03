"""One walk of a captured design, producing the placements a machine needs.

Everything the walk reads is what the runtime resolved during capture:
reference designators are written back by the reverse linker, and the
`soldered` flag has already inherited from its enclosing circuit.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Any

import jitx.log
from jitx.component import Component
from jitx.inspect import extract
from jitx.landpattern import Landpattern
from jitx.layerindex import Side
from jitx.placement import Placement
from jitx.plugin.export import ExportError
from jitx.proxy import typeof
from jitx.units import valuestring

from ..format import BOTTOM, TOP, Part

if TYPE_CHECKING:
    from jitx.run import RuntimeDesign

logger = getLogger(__name__)


def _designator(component: Any, path: Any) -> str:
    """The reference designator, which is what names a part to an operator.

    There is no useful fallback: a placement row whose designator this tool
    invented names a part nobody can find on the board or in the BOM.
    """
    designator = component.reference_designator
    if not designator:
        raise ExportError(
            f"{path} has no reference designator; a placement file is read "
            "against the board and the BOM by designator"
        )
    return str(designator)


def _package(component: Any) -> str:
    """The landpattern's class name, which is what identifies a footprint.

    A component with no landpattern falls back to its own class name, which
    is the most specific thing left to say about it. Two landpattern classes
    of the same name from different modules read the same here; the column
    tells an operator which footprint to expect rather than naming one
    uniquely, so it is not disambiguated.
    """
    landpattern = next(iter(extract(component, Landpattern)), None)
    # landpatterns arrive Proxy-wrapped, so `typeof` is what gets past the
    # proxy to the class the design actually declared
    return typeof(landpattern if landpattern is not None else component).__name__


# `valuestring` renders a quantity with its short unit symbol, and two of
# those symbols are not ASCII. Between them they cover most of the passives
# on a board, and assembly-house upload forms are not reliably UTF-8, so they
# are spelled the way `jitx.units` names them - `uF`, `ohm`, `kohm` - which
# is also how the design that produced the value spells it. `rkm_code` is the
# framework's other renderer and is always ASCII, but it drops the unit
# entirely: `100n` does not say whether it is farads or henries.
_ASCII_UNITS = str.maketrans(
    {
        "\u00b5": "u",  # MICRO SIGN
        "\u03bc": "u",  # GREEK SMALL LETTER MU
        "\u03a9": "ohm",  # GREEK CAPITAL LETTER OMEGA
    }
)


def _value(component: Any) -> str:
    """The value label, in the compact spelling a fab file wants.

    A quantity renders as "15 nanofarad" under `str`; this gives "15 nF".
    """
    value = component.value
    if value is None:
        return ""
    return valuestring(value).translate(_ASCII_UNITS)


def _part(component: Any, trace: Any) -> Part:
    """One component as a placement record, in the design's own frame."""
    designator = _designator(component, trace.path)
    if not trace.transform or not component.transform:
        raise ExportError(
            f"{trace.path} ({designator}) is to be placed but has no "
            "placement; a machine has nowhere to put it"
        )
    # `Trace.transform` is documented as excluding the element's own
    # transform, so the component's placement has to be composed on
    # explicitly; without it every component in a reused subcircuit collapses
    # onto that subcircuit's local coordinates.
    placement = trace.transform * component.transform
    # Side is the composed `Placement.side`, which `Placement._post_mul` has
    # carried through every ancestor multiply. It is not the sign of the
    # determinant: a bottom placement already sets a negative x scale, and a
    # genuinely mirrored component is a separate, orthogonal property.
    side = placement.side if isinstance(placement, Placement) else Side.Top
    return Part(
        designator=designator,
        x=placement.translation[0],
        y=placement.translation[1],
        rotation=placement.rotation,
        mpn=str(component.mpn) if component.mpn else "",
        manufacturer=str(component.manufacturer) if component.manufacturer else "",
        value=_value(component),
        package=_package(component),
        side=BOTTOM if side == Side.Bottom else TOP,
    )


def build(design: RuntimeDesign, *, include_unsoldered: bool = False) -> list[Part]:
    """Every placement in a captured design.

    Components that are not soldered are left out, because a machine places
    what is soldered: `MechanicalComponent`, `NonSolderedComponent` and
    `NonPopulatedComponent` are all absent unless asked for. `soldered` is
    tested against `False` rather than for truthiness because `None` means
    the component defers to its circuit, which the runtime has already
    resolved.

    How many were left out is reported at notice level. A placement file
    that quietly omits a part is worse than one that fails.

    Args:
        design: a captured `RuntimeDesign`.
        include_unsoldered: keep components marked as not soldered.

    Returns:
        One record per placed component, in no order a caller should rely
        on; `render` sorts by designator.

    Raises:
        ExportError: a component to be placed has no reference designator or
            no placement.
    """
    parts: list[Part] = []
    skipped = 0
    for trace, component in design.query(Component):
        if component.soldered is False and not include_unsoldered:
            skipped += 1
            continue
        parts.append(_part(component, trace))
    if skipped:
        jitx.log.notice(
            logger,
            "Left out %d component(s) that are not soldered",
            skipped,
        )
    return parts
