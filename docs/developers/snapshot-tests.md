# Snapshot tests

Gridkeeper has two kinds of tests: unit tests that run anywhere, and shape snapshot tests that build models in Fusion
and compare them with recorded snapshots.

## Unit tests

The geometry math, the settings files, the layouts and the dialog logic are kept free of Fusion where they can be, and
tested with pytest against a stand-in for the Fusion API in `tests/stubs`:

```bash
python -m pytest -q
```

## Shape snapshot tests

Each case in `tests/e2e/cases/` is a JSON file holding the settings of a bin, baseplate or label that differ from the
dialog defaults in `lib/defaultSettings.py`, lengths in mm and angles in degrees. Its snapshot in
`tests/e2e/snapshots/<case>/` has the shapes it built, their fingerprints, every setting they were built with and a
preview picture. The list of cases with their previews is in
[tests/e2e/README.md](https://github.com/Eifel-Joe/FusionGridfinityGenerator/blob/master/tests/e2e/README.md).

### Running them

The test commands are there only when the add-in runs from a **git checkout** with a `.git` folder; releases ship
without it and without them. A `git worktree`, where `.git` is a file, doesn't get them either.

1. Add the checkout as the add-in in **Scripts and Add-Ins**, as in [Installation](../getting-started/installation.md).
2. **Utilities › Add-Ins › Gridkeeper tests: run** opens the test report and builds every case in a document of its
   own.
3. The report shows each case as passed or failed with what differs: the number of bodies, their volume, the box
   around them, a setting that changed. For a failed case you can view the built bodies against the snapshot.

**Gridkeeper tests: update snapshots** records new snapshots after an intended change; it shows what it will replace
and remove before it writes.

![The test palette after running one case: the case passed, its document is left open for Diff, Built and Snapshot](../assets/images/snapshot-test-report.png)

### What a case can check

- **Parameters:** a case can set user parameters once built; the run compares the recomputed bodies with the case
  built with those values from the start.
- **Constraints:** every sketch the generator makes must be fully constrained; label cases and Cullenect cases fail
  otherwise, other cases log such sketches.
- **Part designs:** a case can be built in a part design (`"designIntent": "part"`).
- **Labels:** bins with a text label are compared by their form, not by where each letter lies, which depends on the
  font and the Fusion version. Colored cases check the look of their bodies.

### Adding a case

Write a JSON file into `tests/e2e/cases/` with a `description` and the settings that differ from the defaults, run
**Gridkeeper tests: update snapshots** for it, then rewrite the case list:

```bash
python3 tests/e2e/write_readme.py
```
