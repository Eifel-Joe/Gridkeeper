# Pictures

All pictures in this folder are renders and screenshots from the English Fusion with Gridkeeper 1.0.0.

## German versions (round 60, still to be taken)

The German pages show a German version `name.de.png` (`name-dark.de.gif`) where it exists beside the English
picture, else the English one; raw HTML `<picture>` paths on a German page point one folder higher for the English
picture and to `/de/assets/...` once the German one is there (`tests/test_docs_i18n.py`). Pictures of the add-in's
dialogs and windows get German versions, taken in a German Fusion (or with `languageOverride` = `de`; then Fusion's
own items around them stay English), same state, size and crop as the English one. Models, hover pictures, Fusion's
own interface (Scripts and Add-Ins, Change Parameters, browser, joints) and the snapshot test report stay English.

- [ ] `docs/assets/images`: `bin-lip-dialog`, `context-menu-dark`, `context-menu-light`, `context-menu-export-scene`,
  `dialog-baseplate`, `dialog-baseplate-connection-holes`, `dialog-baseplate-magnet-size`, `dialog-bin`,
  `dialog-bin-compartment-scoops`, `dialog-bin-cullenect`, `dialog-bin-magnet-size`, `dialog-bin-placement`,
  `dialog-bin-placement-cell`, `dialog-bin-scoop-walls`, `dialog-bin-tab-top-offset`, `dialog-box`, `dialog-box-label`,
  `dialog-insert-pocket`, `dialog-label`, `dialog-settings-buttons`, `settings-window`, `update-dialog-available`,
  `updates-dialog-git`, `updates-dialog-installed` (24, `.de.png`)
- [ ] `docs/assets/ui`: the three `bin-*-compartments-*-options` (3, `.de.png`)
- [ ] `docs/assets/gif`: the dialog part of each state of the 15 animations (`dev-notes/tools/anim/raw/<name>/N-dialog.de.png`),
  then `compose.py --language de` for `<name>-dark.de.gif` and `-light.de.gif`; the German captions are in
  `anims.json` (`captionDe`), the model parts are shared
- All of these are taken in Fusion: the pictures above are Fusion screenshots, and the dialog screenshot tool
  (`tools/screenshots/screenshots.py --language de`) draws its own style (torn edges, other scale and crop), so it
  can't make them in the same size and crop

## Own pictures only

Since Gridkeeper 1.0.0 every picture and animation of the documentation is Gridkeeper's own; none is taken over
from GridfinityGenerator. The models in `docs/assets/models` are made from the presets in `tools/screenshots/models`
(since round 58, see `tools/screenshots/README.md`: the palette *Gridkeeper docs: render models*, or a script with
`tools/screenshots/finishPictures.py`), the animations in
`docs/assets/gif` are put together by `dev-notes/tools/anim/compose.py` from rendered models and dialog screenshots
(raw pictures in `dev-notes/tools/anim/raw`, states and captions in `anims.json`).

## Taken (round 58, presets rendered by a Fusion script, see `tools/screenshots/README.md`)

- All 24 model pictures of `docs/assets/models` from their presets in one look (orthographic, `#4A82C8`, 1200 × 900),
  five new: `bin-cullenect-pocket.png` ([Pockets in bins](../../cullenect/pockets.md)), `cullenect-insert.png`
  ([Label inserts](../../cullenect/inserts.md)), `box.png` and `box-label.png` ([Storage boxes](../../boxes.md)),
  `bin-compartments-scoops.png` ([Compartments and scoop](../../bins/compartments.md)).

## Wanted

- Export (upstream round 17.11.2026, p13/p300): the export dialog (shot `fusion-dialog-export`; the click test's one
  shows a folder path with a user name, take it again with a neutral folder), and a 3MF of a bin with a colored label
  and an insert opened in Bambu Studio, for `docs/working/export.md`.

## Taken (click test 17.11.2026, main session)

- `dialog-box.png` (with *Small parts* and **Hinge**), `box-5x4x6.png` (with the orange small parts and a label in its
  holder, round 29), `dialog-box-label.png` (the label dialog): [Storage boxes](../../boxes.md).
- `dialog-bin-magnet-size.png`: [Base, magnets and screws](../../bins/base.md).
- `dialog-baseplate-magnet-size.png`: [Baseplates](../../baseplates.md).
- `bin-lip-dialog.png`: [Body, walls and lip](../../bins/body.md).
- `context-menu-export-scene.png`: [Exporting for printing](../../working/export.md).
- `docs/assets/models/bin-lip-light.png`, `bin-lip-full.png`, `bin-lip-full-untrimmed.png` (lip types, p13): a 1x1x2
  bin cut through its middle, rendered by `fusion-auftraege/ug_lip_render.py`: [Body, walls and lip](../../bins/body.md).

## Taken (click test round 30, main session)

- `box-lid-closed.png`: a box 5 × 4 × 6 with **Lid top** *Closed*, in the view of `box-5x4x6.png`:
  [Storage boxes › Lid](../../boxes.md#lid).

## Taken (round 38, GridfinityGenerator 2.5 merged, click test, main session)

Dialog screenshots in Fusion's dark theme:
- `dialog-bin-placement.png`: the bin dialog's **Placement** group with **Position** *Center on origin* and **Cell**
  empty; `dialog-bin-placement-cell.png`: the same with a cell picked, **Position** greyed out. For
  [Bins › Placement](../../bins/index.md#placement).
- `dialog-bin-tab-top-offset.png`: the **Label tab** group with **Tab top offset** 2 mm. For [Label tab and labels](../../bins/labels.md).
- `dialog-baseplate-connection-holes.png`: a full baseplate, the connection hole inputs greyed out. For [Baseplates](../../baseplates.md).
- `dialog-box.png` again with the group *Lid* (p431), `updates-dialog-installed.png` again after an update, with
  **Reload Gridkeeper** (p450).

## Taken (round 38, rendered by `fusion-auftraege/r38_render.py`)

- `docs/assets/models/bin-magnet-cutouts.png`, `-with-tabs.png`, `-and-screw-holes-with-groove.png` again, with the
  chamfered magnet sockets; `bin-tab-top-offset.png`, `baseplate-padding-connection-holes.png`, `baseplate-magnet-socket-chamfer.png` (cut
  through a socket) new. View, color and
  crop as the pictures of round 26 (orthographic, `#4A82C8`, content plus 20 px).

## Taken (joint origins guide)

- `joint-origins-browser.png`, `dialog-insert-pocket.png`, `joint-bin-into-baseplate.png`, `joints-delete.png`:
  [Components and joints › Joint origins](../../working/components.md#joint-origins), Fusion, master cae4599.

## Taken (update check, PR #4)

- [x] Update check (p310): `update-dialog-available.png`, `updates-dialog-installed.png`, `updates-dialog-git.png`
  for [Installation and updates](../../getting-started/installation.md#update), from the click test of 17.11.2026 with
  a test installation 0.9.0 built from the branch (so they show 0.9.0 → 1.0.0, not Gridkeeper 1.0.0 itself).
