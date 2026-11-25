# Plan round 58, second part: model pictures

Spec: `dev-notes/specs/2026-11-25-r58-model-pictures.md`. Tests: `python -m pytest`; docs: `mkdocs build --strict`.

## Task 1 — Finisher in Python
- [ ] RED `tests/test_finish_pictures.py` (Pillow, skipped without it): content box of a transparent and an opaque
  render, touches-edge flag, fit with margin into the picture size, grading table matches pictureFinish.js (sRGB ↔
  linear), sidecar round trip.
- [ ] GREEN `tools/screenshots/finishPictures.py` (`finish(render, options) -> (image, touchesEdge)`, CLI over a folder).

## Task 2 — Raw render from a script
- [ ] RED unit tests: sidecar contents from a preset (size, margin, supersample, exposure, saturation, output);
  generators bin, baseplate, box, box label, label insert known to the palette.
- [ ] GREEN `commands/commandModelScreenshots/scriptRender.py` (`renderRaw`), `buildModel` for the five generators,
  `presets.DEFAULT_OUTPUT = docs/assets/models`.

## Task 3 — Presets
- [ ] `_docs.json` base; the 19 doc presets extend it; three new ones for the doc pictures without a preset; five new
  ones (Cullenect pocket bin, insert, box, box label, compartments with scoops).
- [ ] Remove the original's presets no page uses, `modelGifs.py`, `modelGifs.json`, `timelines/`.
- [ ] RED/GREEN `tests/test_model_presets.py`: every doc picture has a preset, every preset loads, no preset unused.

## Task 4 — GIFs through compose.py
- [ ] RED tests: Python lookup order (checkout venv, main worktree venv, system Python with Pillow, none), GIF rows
  from `anims.json`, command line of compose.py.
- [ ] GREEN `entry.py`/`picturesPalette.py`; README of `tools/screenshots` rewritten for Gridkeeper.

## Task 5 — Fusion (through the main session)
- [ ] Job `r58_pictures.py`: renderRaw for every doc preset, ~35 s per call, state file, new documents closed unsaved.
- [ ] `finishPictures.py` over the raw folder into `docs/assets/models`; look at each picture.

## Task 6 — Docs
- [ ] New pictures on their pages, `NEEDED.md` updated, CHANGELOG 1.4.0 (Docs), `mkdocs build --strict`, PR draft.
