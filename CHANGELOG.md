# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

Rewritten as a `jitx` CLI export plugin. This is a breaking change in every
direction: the input, the command, and the columns.

### Added

- A `pnp` exporter registered through the `jitx-plugin` entry point, run as
  `jitx design export pnp <design>`. It reads placements out of a built
  design, so there is no intermediate file and no IDE step.
- `Manufacturer` and `Value` columns, both of which the XML carried and the
  old parser dropped.
- `--bottom-rotation {native,negate,flip}`, because the conventions in use
  across the JITX exporters disagree about what a bottom-side angle means.
- `--include-unsoldered`, `--overwrite`.
- `pick_and_place`, a Python API that returns the files it wrote.
- An example board in `examples/`, built from `jitx` alone, whose README
  states the rows it should produce and what each one catches.

### Changed

- Distributed as `jitxlib-pnp` and imported as `jitxlib.pnp`, matching the
  sibling exporters, with the version derived from git rather than pinned in
  two places.
- Components that are not soldered are left out of the file by default.
- Package names come from the design, so a landpattern reads as `Chip0402`
  rather than the `LANDPATTERN0402` the XML flow generated. The `$`-suffix
  truncation that went with those names is gone.
- A component to be placed with no reference designator or no placement is
  now an error rather than a skipped row.

### Removed

- The XML input path. XML export is legacy in py-jitx 4.4, gated behind
  `JITX_EXPERIMENTAL_FEATURES`, and needed a human to run an IDE menu first.
- The standalone `jitx-pnp` command and its stdout mode. The exporter writes
  files and reports them through the jitx log.
- Orphaned JITX project artifacts: build output under `designs/` for a
  module deleted in `af76b3e`, an unreferenced STEP file, committed wheels,
  and VSCode configurations pointing at the design that is gone.

## [0.1.0] - 2026-02-27

- Initial release: a standalone `jitx-pnp` command that parsed a JITX XML
  board export into a pick-and-place table.
