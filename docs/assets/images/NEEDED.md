# Pictures

All pictures in this folder are renders and screenshots from the English Fusion with Gridkeeper 1.0.0.

## Own pictures only

Since Gridkeeper 1.0.0 every picture and animation of the documentation is Gridkeeper's own; none is taken over
from GridfinityGenerator. The models in `docs/assets/models` are rendered by a Fusion script, the animations in
`docs/assets/gif` are put together by `dev-notes/tools/anim/compose.py` from rendered models and dialog screenshots
(raw pictures in `dev-notes/tools/anim/raw`, states and captions in `anims.json`).

## Wanted

- Export (upstream round 17.11.2026, p13/p300): the export dialog (shot `fusion-dialog-export`; the click test's one
  shows a folder path with a user name, take it again with a neutral folder), and a 3MF of a bin with a colored label
  and an insert opened in Bambu Studio, for `docs/working/export.md`.

- Closed lid (round 30, p311): `dialog-box.png` again with the new group *Lid* (after round 31, which changes the
  dialog too). For [Storage boxes](../../boxes.md).

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

## Taken (joint origins guide)

- `joint-origins-browser.png`, `dialog-insert-pocket.png`, `joint-bin-into-baseplate.png`, `joints-delete.png`:
  [Components and joints › Joint origins](../../working/components.md#joint-origins), Fusion, master cae4599.

## Taken (update check, PR #4)

- [x] Update check (p310): `update-dialog-available.png`, `updates-dialog-installed.png`, `updates-dialog-git.png`
  for [Installation and updates](../../getting-started/installation.md#update), from the click test of 17.11.2026 with
  a test installation 0.9.0 built from the branch (so they show 0.9.0 → 1.0.0, not Gridkeeper 1.0.0 itself).
