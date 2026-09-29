"""A small board that exercises every branch of the placement walk.

Nothing here is queried from a parts database, so the example builds with
`jitx` alone and needs no network and no parts cache.

    jitx design export pnp --output demo-pnp.csv examples.demo.PnpDemoDesign

The board is a fixture as much as a demonstration. It carries a part on the
bottom at 45 degrees, which is the only kind of placement that tells the
three bottom-side rotation conventions apart; a part in a subcircuit placed
away from the origin, which catches a walk that forgets to compose the
ancestor frame; a mounting hole, which is mechanical and so belongs in
neither this file nor a BOM; and a part with no manufacturer data at all.

`examples/README.md` states the rows this is expected to produce.
"""

from __future__ import annotations

import jitx.run
from jitx import Board, Circuit, Component, Design, Landpattern, Pad, Port
from jitx.component import MechanicalComponent
from jitx.feature import Cutout
from jitx.landpattern import PadMapping
from jitx.layerindex import Side
from jitx.sample import SampleSubstrate
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Circle, Polyline
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitx.units import kohm, nF

jitx.run.autodetect_design = False


class ChipPad(Pad):
    shape = rectangle(0.6, 0.6)


class TwoPadLand(Landpattern):
    """A two-terminal land, so a chip component can name its pads."""

    p1: Pad
    p2: Pad


class Chip0402(TwoPadLand):
    """A 1.0 x 0.5 mm chip land, origin at the body centre."""

    p1 = ChipPad().at(-0.48, 0.0)
    p2 = ChipPad().at(0.48, 0.0)


class Chip0603(TwoPadLand):
    """A 1.6 x 0.8 mm chip land, origin at the body centre."""

    p1 = ChipPad().at(-0.75, 0.0)
    p2 = ChipPad().at(0.75, 0.0)


class HolePad(Pad):
    """A plated hole: the cutout is what makes it through-hole."""

    shape = Circle(diameter=3.2)

    def __init__(self) -> None:
        self.cutout = Cutout(Circle(diameter=2.2))


class MountingHoleLand(Landpattern):
    p1 = HolePad().at(0.0, 0.0)


class TwoPinSymbol(Symbol):
    """A box with a terminal either side, enough to schematic a chip."""

    a = Pin(at=(-2, 0), length=1, direction=Direction.Left)
    b = Pin(at=(2, 0), length=1, direction=Direction.Right)
    body = Polyline(0.1, [(-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)])


class Chip(Component):
    landpattern: TwoPadLand
    a = Port()
    b = Port()
    symbol = TwoPinSymbol()

    def __init__(self) -> None:
        self += PadMapping({self.a: self.landpattern.p1, self.b: self.landpattern.p2})
        self += SymbolMapping({self.a: self.symbol.a, self.b: self.symbol.b})


class Capacitor0402(Chip):
    reference_designator_prefix = "C"
    landpattern = Chip0402()
    mpn = "CC0402KPX7R8BB104"
    manufacturer = "YAGEO"
    value = 100 * nF


class Resistor0603(Chip):
    reference_designator_prefix = "R"
    landpattern = Chip0603()
    mpn = "RC0603FR-074K7L"
    manufacturer = "YAGEO"
    value = 4.7 * kohm


class Unmarked0402(Chip):
    """A part the design has nothing to say about beyond where it goes."""

    reference_designator_prefix = "C"
    landpattern = Chip0402()


class HoleSymbol(Symbol):
    p = Pin(at=(0, 0), length=1, direction=Direction.Up)
    body = Circle(radius=1)


class MountingHole(MechanicalComponent):
    """Not soldered and not in the bill of materials, so not placed."""

    reference_designator_prefix = "H"
    p = Port()
    landpattern = MountingHoleLand()
    symbol = HoleSymbol()

    def __init__(self) -> None:
        self += PadMapping({self.p: self.landpattern.p1})
        self += SymbolMapping({self.p: self.symbol.p})


class Divider(Circuit):
    """Two parts that travel together, placed as a unit."""

    def __init__(self) -> None:
        self.upper = Resistor0603().at(0.0, 1.0)
        self.lower = Resistor0603().at(0.0, -1.0)
        self.mid = self.upper.b + self.lower.a


class DemoCircuit(Circuit):
    def __init__(self) -> None:
        self.bypass = Capacitor0402().at(-8.0, 6.0, rotate=90.0)
        # the placement that discriminates the bottom-side conventions
        self.underside = Capacitor0402().at(4.0, -6.0, rotate=45.0, on=Side.Bottom)
        self.spare = Unmarked0402().at(-8.0, -6.0)
        self.divider = Divider().at(9.0, 3.0)
        self.hole = MountingHole().at(-18.0, 18.0)

        self.rail = self.bypass.a + self.divider.upper.a + self.spare.a
        self.ground = self.bypass.b + self.divider.lower.b + self.spare.b
        self.bottom_net = self.underside.a + self.underside.b


class DemoBoard(Board):
    shape = rectangle(40, 40)


class PnpDemoDesign(Design):
    """A two-layer demo board for the pick-and-place exporter."""

    board = DemoBoard()
    substrate = SampleSubstrate()
    circuit = DemoCircuit()
