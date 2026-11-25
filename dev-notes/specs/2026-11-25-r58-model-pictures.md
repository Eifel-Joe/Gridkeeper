# Round 58, second part: the model pictures palette for Gridkeeper's docs

Same branch and release as the upstream merge (Gridkeeper 1.4.0).

## Problem

The palette *Gridkeeper docs: render models* (`commands/commandModelScreenshots`, presets in `tools/screenshots/models`)
comes from GridfinityGenerator. Of its 61 presets most belong to the original's README; Gridkeeper's docs show 19 model
pictures (`docs/assets/models`), three of them without a preset, made by one-off scripts in different sizes and looks.
Boxes, Cullenect pockets and inserts have no preset at all. Pictures go to the git-ignored `tools/screenshots/out` of
the loaded checkout. The palette's GIFs fail with *no tools\screenshots\.venv\Scripts\python.exe*: they run the
original's `modelGifs.py` (Playwright) in a venv nobody set up, while Gridkeeper's doc GIFs are made by
`dev-notes/tools/anim/compose.py` (Pillow only). And the palette needs a click: pictures can't be made from a script.

## Decisions

1. **Pictures from a script.** Fusion's Python has no imaging, the palette's page cuts and grades the render
   (`lib/ui/html/pictureFinish.js`). New: `tools/screenshots/finishPictures.py` does the same with Pillow, outside
   Fusion — content box, exposure and saturation in linear light, fit with margin, halving scale-down — on raw renders
   with a JSON sidecar of their options. `commandModelScreenshots.scriptRender.renderRaw(name, folder)` builds a preset,
   frames it and saves the raw render and sidecar, without the palette or a dialog. A Fusion script renders, the
   finisher finishes. The palette keeps its own page and works as before.
2. **Into the docs.** The presets' default output is `docs/assets/models` of the checkout, where the pages take them.
3. **One look.** A `_docs.json` base all doc presets extend: orthographic, Gridkeeper's docs blue `#4A82C8`, shaded
   (without edges, as the docs' pictures before), transparent, 1200 × 900 px, margin 0.05. All 19 doc pictures are made again from presets, the three
   without one get one (`bin-tab-top-offset`, `baseplate-padding-connection-holes`, `baseplate-magnet-socket-chamfer`).
   File names stay, so the pages need no change for them.
4. **New presets** for what the docs don't show as a model yet: a bin with a Cullenect pocket, a Cullenect insert, a
   box 5 × 4 × 6, a box label, a bin with compartments and scoops. The palette builds boxes, box labels and inserts
   too (bins and baseplates only so far). Each picture goes on the page of its feature.
5. **The original's presets go** where no Gridkeeper page or GIF uses them, with `modelGifs.py`, `modelGifs.json` and the
   dialog timelines that only fed it; the dialog screenshot tool (`screenshots.py`, `shots.json`) stays.
6. **GIFs through compose.py.** The palette's GIF rows are the animations of `dev-notes/tools/anim/anims.json`, made
   by `compose.py`, which needs Pillow only. The Python for it is found without a venv of its own: the checkout's
   `tools/screenshots/.venv`, else that of the main checkout of a git worktree, else a Python on the computer that
   has Pillow (`py -3`, `python`); the row says which is missing. README with the setup (`pip install pillow` from PyPI).

## Not part of it

- New GIFs or new model frames for the existing GIFs (their raw pictures stay); new dialog screenshots.
- Pictures in the README.
- Changes to the snapshot previews (they use the same finishing, unchanged).

## End-to-end criterion

pytest green (finisher against known images, preset loading, script render on the stubs); a Fusion job renders every
doc preset by script into raw renders, `finishPictures.py` writes them to `docs/assets/models`, the pictures show the
model whole on a transparent background in one size; `mkdocs build --strict` green; the palette's GIF row for an
animation of `anims.json` runs `compose.py` with the Python found (checked by script, the palette can't be clicked
this round).
