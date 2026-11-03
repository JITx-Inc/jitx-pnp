# Example design

`demo.py` is a two-layer board that exercises every branch of the placement
walk. It is built from `jitx` alone - no parts query, no parts cache, no
network - so it runs anywhere the exporter does.

```console
$ uv pip install -e ..                 # or pip, into the project's venv
$ python -m jitx runtime start --background
$ python -m jitx design export pnp --output demo-pnp.csv examples.demo.PnpDemoDesign
```

## What it should produce

```
RefDes,X,Y,Rotation,PN,Manufacturer,Value,Package,Side
C1,-8.000,6.000,90.000,CC0402KPX7R8BB104,YAGEO,100 nF,Chip0402,Top
C2,4.000,-6.000,45.000,CC0402KPX7R8BB104,YAGEO,100 nF,Chip0402,Bottom
C3,-8.000,-6.000,0.000,,,,Chip0402,Top
R1,9.000,4.000,0.000,RC0603FR-074K7L,YAGEO,4.7 kohm,Chip0603,Top
R2,9.000,2.000,0.000,RC0603FR-074K7L,YAGEO,4.7 kohm,Chip0603,Top
```

Five rows to check, each of which is a different way the walk can go wrong.

**C2 is the important one.** It is the only bottom-side part, and it sits at
45 degrees, which is the only kind of angle that tells the three bottom-side
rotation conventions apart. Expect:

| flag | C2 reads |
|---|---|
| (default) `--bottom-rotation native` | `45.000` |
| `--bottom-rotation negate` | `315.000` |
| `--bottom-rotation flip` | `225.000` |

A square angle there proves nothing: `native` and `negate` agree at 0 and 180
degrees, and `negate` and `flip` agree at 90 and 270.

**R1 and R2 are in a subcircuit.** `Divider` places them at a local (0, +/-1)
and is itself placed at (9, 3), so they belong at (9, 4) and (9, 2). Either
one reading (0, 1) or (0, -1) means the walk reported a component's own
transform without composing the frame it sits in.

**C3 has no manufacturer data**, so those three columns are empty rather than
absent, `N/A`, or the string `None`.

**H1, the mounting hole, is not in the file**, and the run says so:

```
NOTICE  jitxlib.pnp.extract.components  Left out 1 component(s) that are not soldered
```

It is a `MechanicalComponent`, which is not soldered, and a machine places
what is soldered. `--include-unsoldered` brings it back.

**R1 and R2 read `4.7 kohm`, not `4.7 k` followed by an omega.** Pint's short
symbols for ohms and microfarads are outside ASCII, and between them they
cover most of the passives on a board.
