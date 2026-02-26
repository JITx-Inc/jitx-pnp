"""CLI entry point for jitx_pnp.

Usage:
    python -m jitx_pnp <xml_file> [-o OUTPUT] [--split-sides] [--format {csv,tsv,txt}]
"""

import argparse
import sys

from jitx_pnp.pnp import pick_and_place


def main():
    parser = argparse.ArgumentParser(
        prog="jitx_pnp",
        description=(
            "Generate a pick-and-place file from a JITX XML board export. "
            "Extracts component designator, position, rotation, part number, "
            "package, and board side from the XML."
        ),
    )
    parser.add_argument(
        "xml_file",
        help="Path to the JITX XML board export file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="Output file path. If omitted, print to stdout.",
    )
    parser.add_argument(
        "--split-sides",
        action="store_true",
        help=(
            "Write separate files per board side (<stem>_a.<ext> and "
            "<stem>_b.<ext>) instead of a single file with a Side column. "
            "Requires --output."
        ),
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["csv", "tsv", "txt"],
        default="csv",
        help=(
            "Output format (default: csv). "
            "'csv' produces comma-separated values. "
            "'tsv' produces tab-separated values. "
            "'txt' produces a fixed-width column layout."
        ),
    )

    args = parser.parse_args()

    if args.split_sides and not args.output:
        parser.error("--split-sides requires --output")

    result = pick_and_place(
        args.xml_file,
        output_file=args.output,
        split_sides=args.split_sides,
        fmt=args.format,
    )

    if args.output is None:
        sys.stdout.write(result)


if __name__ == "__main__":
    main()
