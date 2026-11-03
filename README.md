# jitx-pnp

Export pick-and-place files from JITX designs.

Distributed as `jitxlib-pnp`, importable as `jitxlib.pnp`. It registers a
`pnp` exporter with the `jitx` CLI, which reads placements straight out of a
built design - there is no intermediate file and no IDE step, so it runs in
CI.

Requires `jitx>=4.6`.

## Install

```console
pip install -e .
```

Run this in the project's environment, the one holding the design to export
and its own `jitx`. It registers the `pnp` exporter with that `jitx`:

```console
python -m jitx design export --help     # must list "pnp"
```

If it does not, the `jitx` being run is a different install from the one the
package went into - most often the global CLI rather than the project's.
Plugin discovery is an entry-point lookup in whichever interpreter runs
`jitx`, so `python -m jitx` from the project's venv is the reliable spelling.

## Usage

With a jitx runtime running in the project:

```console
python -m jitx design export pnp --output pnp.csv examples.demo.PnpDemoDesign
```

```
RefDes,X,Y,Rotation,PN,Manufacturer,Value,Package,Side
C1,-8.000,6.000,90.000,CC0402KPX7R8BB104,YAGEO,100 nF,Chip0402,Top
C2,4.000,-6.000,45.000,CC0402KPX7R8BB104,YAGEO,100 nF,Chip0402,Bottom
C3,-8.000,-6.000,0.000,,,,Chip0402,Top
R1,9.000,4.000,0.000,RC0603FR-074K7L,YAGEO,4.7 kohm,Chip0603,Top
R2,9.000,2.000,0.000,RC0603FR-074K7L,YAGEO,4.7 kohm,Chip0603,Top
```

That is the board in `examples/`, whose README says what each row is there
to catch.

Without `--output` the file is named after the design in the current
directory, as `<design>-pnp.csv`.

| Field | |
|---|---|
| `RefDes` | Reference designator, assigned by the runtime |
| `X`, `Y` | Millimetres, in the design's own frame |
| `Rotation` | Degrees counter-clockwise; see [Bottom-side rotation](#bottom-side-rotation) |
| `PN` | Manufacturer part number |
| `Manufacturer` | |
| `Value` | The component's value label, e.g. `100 nF`, `4.7 kohm` |
| `Package` | The landpattern's class name |
| `Side` | `Top` or `Bottom` |

Rows are sorted naturally by designator, so `C2` precedes `C10`. Coordinates
are the design origin unshifted, which is what the sibling exporters emit, so
a placement file and a fab image of the same board agree with each other.

### Options

| Flag | Default | |
|---|---|---|
| `--output PATH` | `<design>-pnp.<ext>` in the working directory | The file to write |
| `--format {csv,tsv,txt}` | `csv` | `txt` is fixed-width columns, for reading |
| `--split-sides` | off | One file per populated side |
| `--bottom-rotation {native,negate,flip}` | `native` | See below |
| `--include-unsoldered` | off | Keep parts that are not soldered |
| `--overwrite` | off | Replace files that are already there |

`--split-sides` writes `<stem>_top<suffix>` and `<stem>_bottom<suffix>` and
not the combined file, drops the `Side` column that the names now carry, and
skips a side with nothing on it. The suffix comes from `--output`, not from
`--format`, so `--output pnp.csv --format txt` writes fixed-width text into a
file called `pnp.csv`.

### Bottom-side rotation

A top-side angle is the design's own angle. A bottom-side one depends on
which way the reader flips the board to look at it, and the conventions in
use disagree:

| `--bottom-rotation` | bottom angle | used by |
|---|---|---|
| `native` (default) | `r` | this library; the `Side` column carries the rest |
| `negate` | `-r` | `jitxlib-jlcpcb`, writing a JLCPCB CPL |
| `flip` | `r + 180` | Gerber X3 `.CRot`, Siemens Xpedition |

The default reports what the design says, because this library is
fab-agnostic and a house convention belongs in that house's library. Pick the
one your machine expects, and check it against a part placed at an angle that
is not a multiple of 90: `native` and `negate` agree at 0 and 180 degrees,
and `negate` and `flip` agree at 90 and 270, so a square angle cannot tell
them apart. `examples/` has a board built for exactly this check.

### Which parts are in the file

Components that are not soldered are left out, because a machine places what
is soldered: `MechanicalComponent`, `NonSolderedComponent` and
`NonPopulatedComponent` (do-not-populate) are all absent by default.
`--include-unsoldered` keeps them.

A component that is to be placed but has no reference designator, or no
placement, is an error rather than a skipped row. A placement file that
quietly omits a part is worse than one that fails.

## Python API

`pick_and_place` takes a captured design and returns the files it wrote,
which is the part the CLI cannot give you:

```python
import jitx
from jitxlib.pnp import pick_and_place
from my.boards import Widget

with jitx.runtime as runtime:
    design = runtime.submit(Widget)
    design.capture()
    written = pick_and_place(design, output="pnp.csv", split_sides=True)
```

## Migrating from the XML flow

This used to be a standalone `jitx-pnp` command that parsed an XML board
export produced from the IDE's export menu. That flow is gone: XML export is
legacy in py-jitx 4.4, gated behind an experimental-features environment
variable, and it needed a human to run a menu before the tool could start.

- `jitx-pnp board.xml -o pnp.csv` becomes
  `python -m jitx design export pnp --output pnp.csv my.boards.Widget`.
- There is no standalone command and no stdout mode. The exporter writes
  files and reports them through the jitx log.
- Two columns are new: `Manufacturer` and `Value`. `Side` is still last, so
  `--split-sides` still drops exactly that one.
- Package names come from the design now, so a landpattern reads as
  `Chip0402` rather than as the `LANDPATTERN0402` the XML flow generated.
- Parts that are not soldered used to be in the file and are not any more.

## Compatibility

Tested against the 4.6.0 release: `jitx` 4.6.0, `jitxcore` 4.6.0 and the
production native runtime 4.6.0, on Python 3.12. `VALIDATION.md` records the
commands and results.

`jitx` 4.6.0 is on the JITX package feed; public PyPI still serves 4.4.3,
so installing needs that feed as an extra index until 4.6 is mirrored:

```console
pip install --extra-index-url https://pypi.jitx.com/jitx/main/+simple -e .
```

CI sets the same index through `PIP_EXTRA_INDEX_URL`.

4.6 moved `RuntimeDesign.root`, `.nets` and `.layers` to read-only
properties and left the callable `nets()` / `layers()` forms as warning
shims. This exporter calls none of them, and its suite turns deprecation and
runtime warnings into failures so it stays that way. The rows it writes
still match the ones `examples/README.md` recorded before the move.

## Development

```console
hatch test              # pytest; the format layer needs no runtime
hatch fmt --check       # ruff
hatch run types:check   # pyright
```

Two layers, strictly separated: `format/` renders a table and imports no
jitx, so the writers and the rotation rule are testable without a runtime;
`extract/` walks a captured `RuntimeDesign`. `CLAUDE.md` has the conventions.

## License

MIT.
