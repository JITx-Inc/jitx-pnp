# jitx-pnp

Generate pick-and-place (PnP) files from JITX XML board exports.

## Overview

This tool parses the XML that JITX exports from a board design and produces a
pick-and-place file listing every component's placement data:

| Field    | Description                        |
|----------|------------------------------------|
| RefDes   | Reference designator (e.g. C1, U3) |
| X        | X coordinate in mm                 |
| Y        | Y coordinate in mm                 |
| Rotation | Rotation angle in degrees          |
| PN       | Manufacturer part number (MPN)     |
| Package  | Landpattern / package name         |
| Side     | Board side (Top or Bottom)         |

## Installation

Requires Python 3.12+.

Install directly from GitHub:

```bash
pip install git+https://github.com/JITx-Inc/jitx-pnp.git
```

For development:

```bash
git clone https://github.com/JITx-Inc/jitx-pnp.git
cd jitx-pnp
pip install -e .
```

> **Note:** This package will be published to PyPI in the future. Once
> available, you will be able to install it with `pip install jitx-pnp`.

## Exporting XML from JITX

In the JITX IDE, use the export menu to generate an XML file for your board
design. The resulting file will have a `<PROJECT>` root element containing a
`<BOARD>` section with component instances and a `<SCHEMATIC>` section with
part number data.

## Usage

### Command line

```
jitx-pnp <xml_file> [-o FILE] [-f {csv,tsv,txt}] [--split-sides]
```

**Print CSV to stdout:**

```bash
jitx-pnp board.xml
```

```
RefDes,X,Y,Rotation,PN,Package,Side
C1,63.457,110.056,90.000,CGA2B3X7R1H103M050BB,Pkg0402,Top
C10,39.292,70.994,90.000,04023D105KAT2A,Pkg0402,Top
...
```

**Write to a file:**

```bash
jitx-pnp board.xml -o pnp.csv
```

**Tab-separated output:**

```bash
jitx-pnp board.xml -f tsv -o pnp.tsv
```

**Fixed-width text table:**

```bash
jitx-pnp board.xml -f txt
```

```
REF DES  X COORD  Y COORD  ROT      PN                     PACKAGE  SIDE
-------  -------  -------  -------  ---------------------  -------  ----
C1       63.457   110.056  90.000   CGA2B3X7R1H103M050BB   Pkg0402  Top
C10      39.292   70.994   90.000   04023D105KAT2A         Pkg0402  Top
...
```

**Split output by board side:**

```bash
jitx-pnp board.xml -o pnp.csv --split-sides
```

This writes `pnp_top.csv` and `pnp_bottom.csv` (if components exist on that
side), each without the Side column since it is implicit in the filename.

The `python -m jitx_pnp` invocation also works as an alternative to the
`jitx-pnp` command.

### Python API

```python
from jitx_pnp import pick_and_place

# Return CSV string
csv_text = pick_and_place("board.xml")

# Write to file
pick_and_place("board.xml", output_file="pnp.csv")

# Fixed-width format, split by side
pick_and_place("board.xml", output_file="pnp.txt", fmt="txt", split_sides=True)
```

## Options reference

| Option | Description |
|---|---|
| `xml_file` | Path to the JITX XML board export (required) |
| `-o`, `--output FILE` | Write output to FILE instead of stdout |
| `-f`, `--format {csv,tsv,txt}` | Output format (default: `csv`) |
| `--split-sides` | Write separate files per board side (requires `--output`) |
| `-h`, `--help` | Show help and exit |

## How it works

1. Parses `BOARD/INST` elements for placement data (position, rotation, side,
   package name).
2. Parses `SCHEMATIC/.../SCH-INST/PROPS` elements for part numbers (MPN),
   joining to board instances by reference designator.
3. Sorts components by reference designator and writes the output in the
   requested format.

## License

MIT
