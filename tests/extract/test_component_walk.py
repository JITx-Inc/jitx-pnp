"""The component walk, driven by `jitx.test.TestCase`.

Everything else about a placement is tested through the format layer, which
needs no design. This file covers the half that is otherwise reachable only
by a live export: the walk that turns a design into records.

`jitx.test.TestCase` enables instantiation, which is what makes a component
exist outside a runtime at all. What it does not give is anything the
runtime computes, so the fixtures below assign their own reference
designators; normally the reverse linker writes them back during capture.

JITX classes must be defined at module scope. Creating one inside a test
case instantiates its members as class members instead of taking them
through instantiation, which `jitx.test` warns about and `_structural`
refuses outright.
"""

from __future__ import annotations

import jitx.run
import jitx.test
import pytest
from jitx import Board, Circuit, Component, Design, Landpattern, Pad
from jitx.component import NonSolderedComponent
from jitx.landpattern import PadMapping
from jitx.layerindex import Side as JitxSide
from jitx.net import Port
from jitx.plugin.export import ExportError
from jitx.query import query
from jitx.run.runtime import RuntimeDesign
from jitx.sample import SampleSubstrate
from jitx.shapes.composites import rectangle
from jitx.units import kohm, nF, uF

from jitxlib.pnp.extract.components import _value, build
from jitxlib.pnp.format import BOTTOM, TOP

# this module defines a Design, and importing it would otherwise trip the
# "we're attempting to run a JITX design file" entry-point autodetection
jitx.run.autodetect_design = False


class ChipPad(Pad):
    shape = rectangle(0.6, 0.6)


class Chip0402(Landpattern):
    p1 = ChipPad().at(-0.5, 0.0)
    p2 = ChipPad().at(0.5, 0.0)


class Chip0603(Landpattern):
    p1 = ChipPad().at(-0.8, 0.0)
    p2 = ChipPad().at(0.8, 0.0)


class TwoPin(Component):
    a = Port()
    b = Port()
    landpattern = Chip0402()

    def __init__(self) -> None:
        self += PadMapping({self.a: self.landpattern.p1, self.b: self.landpattern.p2})


class Bigger(TwoPin):
    landpattern = Chip0603()


class Unsoldered(NonSolderedComponent):
    a = Port()
    b = Port()
    landpattern = Chip0402()

    def __init__(self) -> None:
        self += PadMapping({self.a: self.landpattern.p1, self.b: self.landpattern.p2})


class Nested(Circuit):
    """A subcircuit placed away from the origin, to be reused.

    Its component sits at a local offset and takes no side of its own, so a
    walk that forgets to compose the ancestor frame reports the offset
    rather than the board position, and one that reads the component's own
    side reports the wrong side for the instance placed underneath.
    """

    def __init__(self, designator: str) -> None:
        self.inner = TwoPin().at(1.0, 0.0)
        self.inner.reference_designator = designator


class WalkCircuit(Circuit):
    def __init__(self) -> None:
        self.top = TwoPin().at(-5.175, 4.12, rotate=270.0)
        self.top.reference_designator = "C1"
        self.top.mpn = "04025A150FAT2A"
        self.top.manufacturer = "AVX"
        self.top.value = 15 * nF

        self.bottom = Bigger().at(2.0, -3.0, rotate=45.0, on=JitxSide.Bottom)
        self.bottom.reference_designator = "C2"

        self.nested = Nested("C3").at(6.0, 6.0)
        self.flipped = Nested("C4").at(-6.0, -6.0, on=JitxSide.Bottom)

        self.dnp = Unsoldered().at(8.0, 8.0)
        self.dnp.reference_designator = "R9"


class WalkBoard(Board):
    shape = rectangle(24, 20)


class WalkDesign(Design):
    board = WalkBoard()
    substrate = SampleSubstrate()
    circuit = WalkCircuit()


class Nameless(Circuit):
    def __init__(self) -> None:
        self.orphan = TwoPin().at(0.0, 0.0)


class NamelessDesign(Design):
    board = WalkBoard()
    substrate = SampleSubstrate()
    circuit = Nameless()


class _Valued:
    """Just enough of a component for the value renderer to read."""

    def __init__(self, value: object) -> None:
        self.value = value


class StaticDesign[T: Design](RuntimeDesign[T]):
    """A `RuntimeDesign` over a design that was never sent to a runtime.

    The query is the real one - `jitx.query.query`, which is what
    `RuntimeDesign.query` delegates to - so transformers, `opaque` and the
    accumulated transform behave as they do in an export. `nets` is left
    alone because a placement file has no use for it.
    """

    def __init__(self, root: T) -> None:
        self.root = root

    @property
    def name(self) -> str:
        return "static"

    def query(self, target, /, **kwargs):
        return query(self.root, target, **kwargs)


class ComponentWalk(jitx.test.TestCase):
    """One walk, shared by the assertions below.

    Built per test rather than once for the class: `build` is supposed to be
    a pure function of the design, and a walk that only works the first time
    is a bug this would otherwise hide.
    """

    def walk(self, **kwargs):
        return {
            part.designator: part
            for part in build(StaticDesign(WalkDesign()), **kwargs)
        }

    def test_a_top_side_component_keeps_its_own_placement(self) -> None:
        part = self.walk()["C1"]
        assert (part.x, part.y) == pytest.approx((-5.175, 4.12))
        assert part.rotation == pytest.approx(270.0)
        assert part.side == TOP

    def test_a_bottom_side_component_is_reported_on_the_bottom(self) -> None:
        """Side is the composed `Placement.side`, not the sign of a scale."""
        part = self.walk()["C2"]
        assert part.side == BOTTOM
        assert part.rotation == pytest.approx(45.0)

    def test_a_component_in_a_placed_subcircuit_lands_on_the_board(self) -> None:
        """`trace.transform * comp.transform`, in that order.

        The inner component sits at (1, 0) inside a circuit placed at
        (6, 6). A walk that reports the component's own transform alone puts
        it at (1, 0), which is the failure this fixture exists for.
        """
        part = self.walk()["C3"]
        assert (part.x, part.y) == pytest.approx((7.0, 6.0))

    def test_a_subcircuit_placed_underneath_takes_its_contents_with_it(
        self,
    ) -> None:
        """`Placement.side` composes through every ancestor multiply.

        C4 declares no side of its own; it is on the bottom because the
        circuit holding it is.
        """
        part = self.walk()["C4"]
        assert part.side == BOTTOM

    def test_a_component_that_is_not_soldered_is_left_out(self) -> None:
        assert "R9" not in self.walk()

    def test_an_unsoldered_component_can_be_asked_for(self) -> None:
        assert "R9" in self.walk(include_unsoldered=True)

    def test_the_part_number_and_its_neighbours_come_off_the_component(self) -> None:
        part = self.walk()["C1"]
        assert part.mpn == "04025A150FAT2A"
        assert part.manufacturer == "AVX"

    def test_a_quantity_reads_the_way_a_fab_file_spells_it(self) -> None:
        """`str` on a pint quantity gives "15 nanofarad"."""
        assert self.walk()["C1"].value == "15 nF"

    def test_a_unit_that_is_not_ascii_is_spelled_out(self) -> None:
        """Ohms and microfarads cover most of the passives on a board, and
        pint's symbols for both are outside ASCII."""
        assert _value(_Valued(4.7 * kohm)) == "4.7 kohm"
        assert _value(_Valued(1 * uF)) == "1 uF"

    def test_a_value_that_is_already_text_is_left_alone(self) -> None:
        assert _value(_Valued("DNP")) == "DNP"
        assert _value(_Valued(None)) == ""

    def test_a_component_with_nothing_to_say_says_nothing(self) -> None:
        part = self.walk()["C2"]
        assert (part.mpn, part.manufacturer, part.value) == ("", "", "")

    def test_the_package_is_the_landpattern_class(self) -> None:
        walked = self.walk()
        assert walked["C1"].package == "Chip0402"
        assert walked["C2"].package == "Chip0603"

    def test_one_landpattern_class_is_one_package_name(self) -> None:
        walked = self.walk()
        assert walked["C1"].package == walked["C3"].package

    def test_a_component_with_no_designator_is_named_rather_than_invented(
        self,
    ) -> None:
        with pytest.raises(ExportError, match="no reference designator"):
            build(StaticDesign(NamelessDesign()))
