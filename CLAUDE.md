# Preamble

This package exports pick-and-place files from JITX designs through the
jitx-plugin export entry point, registered as `pnp`. It is distributed as
`jitxlib-pnp` and imports as `jitxlib.pnp`.

`jitxlib-gerber` is the template for everything structural here - the plugin
module, the two-layer split, the packaging and the test shapes. Read it
before inventing something. `jitx-exporter-guidance` is the cross-exporter
reference for what each JITX release changes under an exporter; read its
handbook and compatibility record before a version bump.

The repo carried a standalone XML parser until the migration to this layout.
It is gone: XML export is legacy in py-jitx 4.4 and gated behind
`JITX_EXPERIMENTAL_FEATURES`. Do not reintroduce a file-parsing input path.

# Architecture

Two layers, strictly separated, as in jitxlib-gerber and jitxlib-odb:

- `src/jitxlib/pnp/format/`: renders placements as a table. No jitx imports
  anywhere in this package; fully unit-testable without a runtime. This is
  where the bottom-side rotation rule lives.
- `src/jitxlib/pnp/extract/`: walks a captured `RuntimeDesign` via the jitx
  query APIs and populates `format`'s records.

A `Part` carries the design's own angle and a `"Top"` / `"Bottom"` string,
never a `jitx.layerindex.Side`. Extract natively and convert at the writer:
that keeps `format` jitx-free and keeps one convention from leaking into the
walk.

Imports in `__init__.py` are absolute. A relative `from .format import` there
binds `format` in the file, which is also the name of the flag that selects a
layout, and pyright reads the two as one symbol.

# Targeting JITX 4.6

The floor is `jitx>=4.6,<5`. What 4.6 changed that reaches this package:

- `RuntimeDesign.root`, `.nets` and `.layers` are read-only properties
  backed by private submission state. The test stand-in shadows `root` with
  a property of its own rather than assigning it, and does not call the base
  `__init__`, whose state object wants a `ReverseMapper` there is no runtime
  to produce. `query`, `submit` and `capture` are still methods.
- The callable `nets()` / `layers()` shims emit `RuntimeWarning`. Nothing
  here calls them, and `filterwarnings` in `pyproject.toml` makes that
  category an error so it cannot creep in quietly.
- `jitx.units.valuestring` arrived, and is what renders the `Value` column.
  Its sibling `rkm_code` is always ASCII but drops the unit - `100n` does
  not say farads or henries - so it is not used here.
- The CLI's default log level moved from NOTICE to INFO. Results still go
  out through `jitx.log.notice`, which is above both.

Nothing in the exported data moved: `query`, `Placement.side` composition,
and the `soldered` flag behave as they did on 4.4. 4.6 contracts that do not
reach a placement file - canonical net names through `design.nets.find`,
implicit `PadMapping` / `SymbolMapping` capture, via spans and backdrills,
routing diagnostics - are in the guidance handbook if this ever grows a
column that needs them.

# Transforms

A component's placement is `trace.transform * comp.transform`, in that order.
`Trace.transform` is documented as excluding the element's own transform, so
without the composition every component in a reused subcircuit reports that
subcircuit's local coordinates.

Side is the composed `Placement.side`, which `Placement._post_mul` carries
through every ancestor multiply. It is not the sign of the determinant: a
bottom placement already sets a negative x scale, and a genuinely mirrored
component is a separate, orthogonal property. Never apply a side flip on top
of the one a placement already carries.

`soldered` and `in_bom` are `bool | None`, where `None` means the component
defers to its enclosing circuit and the runtime has already resolved the
chain. Test against `False`, never for truthiness.

# Bottom-side rotation

Three conventions are in use across the JITX exporters and they disagree:
`jitxlib-jlcpcb` writes `-r`, Gerber X3's `.CRot` and Xpedition write
`r + 180`, and the design says `r`. This library is fab-agnostic, so `native`
is the default and a house convention belongs in that house's library.

`native` and `negate` agree at 0 and 180 degrees; `negate` and `flip` agree
at 90 and 270. Anything that checks a bottom-side angle must use an angle
that is not a multiple of 90, or it discriminates nothing. The example board
places a part at 45 degrees for this.

# Docstrings vs implementation notes

Docstrings are public API help: how to use a class or function and its
purpose, parameter semantics, return shape, preconditions, units and
coordinate frames, and the errors raised. Nothing else.

Implementation detail goes in `#` comments, never in docstrings: how it works
internally, discoveries and quirks about how JITX data marshals onto a
placement row, pyright convention notes, and design-rationale asides.
Docstrings surface as hover text in language servers, so keep them about use,
not mechanism.

Use Google-style `Args:` and `Returns:` on every public callable, which is
what `jitx-engineering-review` checks. Do not repeat types in prose; they
belong in the signature, and neither section is a place to restate a default.
Say what a parameter constrains and what the caller actually gets: that
`legal_stem` can fold two names together, that `build`'s order is not one to
rely on. If an entry would only name the argument again, the docstring is
not the problem - find the thing about it a caller could get wrong.

Test rationale goes in `#` comments, not docstrings. A test is not shipped
documentation, and an `Args:` entry for a pytest fixture says nothing.

Be terse. No bold, no em-dashes, no emoji - in docstrings, commit messages
and PR descriptions alike. No tool-advertising trailers in commits either;
disclose AI authorship plainly in the PR body instead.

Type-annotate everything except `self`. `type: ignore` and `noqa` are
prohibited unless justified in an adjacent comment. Do not lower pyright
below "standard".

# The plugin module

`plugin.py` has three constraints that are each load-bearing:

- **No `from __future__ import annotations`.** The CLI builds its options
  from `inspect.signature(plugin.export)`, and with postponed evaluation
  every annotation arrives as a string typer cannot resolve, which fails the
  whole `design export` command group rather than just this plugin.
- **`preflight` and `export` must carry identical keyword signatures.** The
  CLI passes the same kwargs to both.
- **Module scope imports only jitx.** The plugin registry imports this module
  on every `jitx` invocation, so anything heavier is imported inside the
  call.

Flags are the keyword parameters of `export`, the subcommand name is the
string passed to `register`, and the `--help` text is the class docstring.
Adding a flag means adding a parameter. Results go out through
`jitx.log.notice`, which reaches the run log as well as the console, unlike
`print`.

# Preparation

Install with `pip install -e .` into the project's environment, the one
holding the design and its own `jitx`. `python -m jitx design export --help`
must list `pnp`; if it does not, the `jitx` being run is a different install
from the one the package went into.

# Exporting

A running jitx runtime is needed in the project being exported:

```
python -m jitx design export pnp [--output <path>] [--format csv|tsv|txt] \
    [--split-sides] [--bottom-rotation native|negate|flip] \
    [--include-unsoldered] [--overwrite] <design>
```

# Validation

- `hatch test`, `hatch fmt --check`, `hatch run types:check` must all be
  clean. Deprecation and runtime warnings fail the suite; do not silence a
  category to get a run green.
- `VALIDATION.md` records the versions and commands behind the current
  compatibility claim. Update it on a version bump rather than restating
  results in a commit message.
- `tests/format/` imports no jitx and covers the writers and the rotation
  rule. `tests/extract/` uses `jitx.test.TestCase` with a `RuntimeDesign`
  subclass over the real `jitx.query`, so the walk runs the same code an
  export runs without needing a runtime.
- `examples/README.md` states the rows the example board is expected to
  produce, and why each one is there. It is the end-to-end acceptance test;
  run it against a real runtime before shipping a change to the walk.
