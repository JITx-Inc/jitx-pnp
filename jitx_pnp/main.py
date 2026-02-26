from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts import ResistorQuery, Resistor
from jitx.units import ohm, kohm


class Resistors(Circuit):
    r1 = Resistor(resistance=100 * ohm)
    r2 = Resistor(resistance=2 * kohm)
    nets = [r1.p1 + r2.p1, r1.p2 + r2.p2]


class jitx_pnp(SampleDesign):
    resistor_defaults = ResistorQuery(case="0402", tolerance=0.01)
    circuit = Resistors()
