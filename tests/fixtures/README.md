# Test fixtures

## `synthetic.xml`

Hand-crafted minimal `<PROJECT>` XML that exercises every code path in
`jitx_pnp.pnp._parse_instances`: natural sort across multi-digit
designators, side normalization (mixed case + unknown), missing
`DESIGNATOR` skip, missing `POSE` skip, non-numeric `POSE` fields,
multi-unit `SCH-INST` deduplication, package `$` truncation, and
CSV-injection sanitization for both `=` and `+` prefixed MPNs.

Edit by hand. Keep it tiny — it is the contract that documents
expected parser behavior.

## `golden.xml` and `golden.csv`

End-to-end fixture: a real JITX-produced XML export and the CSV
`pick_and_place()` should produce from it. Used by `test_golden.py`.

`golden.xml` is **not** committed by default. The integration test
auto-skips when it is missing, so the test suite stays green for
contributors who do not have the JITX IDE installed.

### Regenerating the golden fixture

Run from the repo root:

```bash
# 1. Build the bundled JITX design.
python -m jitx build jitx_pnp.main.jitx_pnp

# 2. Export the XML from the JITX IDE
#    (File → Export, per the project README), then save it as:
cp /path/to/exported.xml tests/fixtures/golden.xml

# 3. Regenerate the expected CSV from the new XML.
jitx-pnp tests/fixtures/golden.xml -o tests/fixtures/golden.csv

# 4. Inspect the diff before committing.
git diff tests/fixtures/golden.csv
```

Re-run after any change to `jitx_pnp/pnp.py` that intentionally alters
the output format.
