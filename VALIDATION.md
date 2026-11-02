# Validation record

What was run, on what, and what was not. Update this on a version bump
rather than restating results in a commit message.

## Baseline

Checked November 2, 2026, against the released 4.6 artifacts. The Python
packages and the native runtime carry independent version sequences, and a
lockfile does not select the native runtime: this used `--prod`, which is
the channel a customer on the release build has.

`jitx` 4.6.0 is on the JITX main feed. Public PyPI still serves 4.4.3, so
installing from PyPI alone will not satisfy the floor this package declares
until 4.6 is mirrored there.

| Artifact | Version |
| --- | --- |
| Python | 3.12.13 |
| `jitx` | 4.6.0 |
| `jitxcore` | 4.6.0 |
| Native runtime | 4.6.0, from `jitx runtime update --prod`, confirmed by `jitx runtime introspect` as `release` |

The previous record for this package was `jitx` 4.4.2 with native 4.4.1.
An earlier pass of this migration ran on native 4.6.0-rc.16; the results
below are from the production 4.6.0 runtime that replaced it.

## What 4.6 changed under this exporter

| Change | Effect here |
| --- | --- |
| `RuntimeDesign.root` is a read-only property over private submission state | The test stand-in shadows it with a property instead of assigning it, and does not call the base `__init__`. Twelve extract tests failed before the change; none after. |
| `nets()` / `layers()` callable shims warn | Not called. `filterwarnings` makes `RuntimeWarning`, `DeprecationWarning` and `PendingDeprecationWarning` errors so this stays true. |
| `jitx.units.valuestring` added | Renders the `Value` column, replacing a local quantity format. Output is unchanged for every value in the example board, which covers nanofarads, kilohms and three empty cells. |
| CLI default log level NOTICE to INFO | No effect. Results go out at notice, which both levels show. |
| Plugin interface, registry, CLI export wiring | Byte-identical to 4.4. `jitx/plugin/export.py`, `jitx/plugin/_registry.py` and `jitx/_cli/design/export.py` all diff empty. |

4.6 contracts that do not reach a placement file were read but not exercised:
canonical net names through `design.nets.find`, implicit `PadMapping` and
`SymbolMapping` capture, via spans and backdrill soldermask openings,
`Conductor.roughness` units, and `DroppedRoute` / `UnsquiggledRoute`
diagnostics. This exporter reads none of them. A column that needs one is a
reason to revisit this list.

## Commands and results

```console
hatch test              48 passed
hatch fmt --check       17 files already formatted, ruff check clean
hatch run types:check   0 errors, 0 warnings, 0 informations
hatch build             sdist and wheel; twine check PASSED for both
```

The built wheel declares `Requires-Dist: jitx<5,>=4.6` and the
`jitx-plugin` entry point `export = jitxlib.pnp.plugin`.

Plugin discovery, from the project venv:

```console
python -m jitx design export --help     # lists pnp
```

Live export against the running native runtime, `examples.demo.PnpDemoDesign`:

| Command | Result |
| --- | --- |
| `--output demo.csv` | Five rows, diffed clean against the rows `examples/README.md` recorded before the migration. The mounting hole is absent and the run says so at notice level. |
| `--bottom-rotation native\|negate\|flip` | C2 reads `45.000`, `315.000`, `225.000`. |
| `--split-sides` | Writes `s_top.csv` and `s_bottom.csv`, drops the `Side` column, and does not write `s.csv`. |
| `--split-sides` over existing files | Refuses with `Output path .../s_top.csv already exists and overwrite was not specified`, exits 1, and leaves both files untouched. |
| `--format txt --include-unsoldered` | Fixed-width columns, H1 present. |

The comparison is against `examples/README.md` as it stood at 932a4bf,
which is the pre-migration record of what this board exports. The 4.4
artifacts themselves were not kept, so this says the fields agree with what
was written down, not that two files were compared byte for byte.

## Gates not run

- Python 3.13. The CI matrix covers it; this record is 3.12 only.
- CI itself has not run against 4.6.
- No consumer was exercised. The columns are checked against the example
  board's documented rows, not against a pick-and-place machine or an
  assembly house's import.
- No customer design was exported. The example board is the only fixture
  with a live runtime behind it.
