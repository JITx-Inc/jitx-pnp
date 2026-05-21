# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-30

### Added

- Initial release.
- `pick_and_place()` Python API: parse a JITX XML board export and emit
  pick-and-place data as CSV, TSV, or fixed-width text.
- `jitx-pnp` console script and `python -m jitx_pnp` module entry point.
- `--split-sides` option to write separate top/bottom files (omitting
  the `Side` column when split).
- Natural sort of reference designators (so `C2` precedes `C10`).
- CSV-injection sanitization on `MPN` and `Package` fields.
- Test suite covering helpers, parser, writers, public API, and CLI.
- GitHub Actions CI: tests on Python 3.12 and 3.13, ruff lint/format,
  and `python -m build` + `twine check`.

[Unreleased]: https://github.com/JITx-Inc/jitx-pnp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/JITx-Inc/jitx-pnp/releases/tag/v0.1.0
