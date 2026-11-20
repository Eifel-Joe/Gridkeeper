# Round 54 – a centered bin stays centered when its base units change (p670)

Status 2026-11-20. Point p670 "Centered bin doesn't stay centered when the grid size changes" (bug), patch 1.2.1.
Branch `r54-centered-bin-follows-grid` from `master` 26814d2 (release 1.2.0).

## Finding

A bin with **Center on origin** is built from the origin into +X and +Y and then moved by the feature
`Bin placement` (`placementUtils.moveBodies`). The offset comes from `centeredPlacement(state)`, plain numbers
(`ValueInput.createByReal`): `-(binWidth × baseWidth − 2 × clearance) / 2`, the same for Y. The bin's geometry follows
`gfBinN_baseWidth` / `gfBinN_baseLength`, the move doesn't. Set the base width from 42 to 50 mm in Fusion's parameter
table and the 2×1 bin grows to the right from its old left edge (−41.75 mm): known from rounds 51/52, feet at −17/33
instead of symmetrical. Upstream has the same code (`centeredPlacement`, `moveBodies` with `createByReal`).

The same constant offset goes into everything placed after the move, with the bin:

- the foot joint origins (`footCenters(..., Dim.length(binPlacement[0]), ...)`),
- the Cullenect pocket joint origins (`Dim.length(binPlacement[0])`),
- the colored label letters, drawn at the bin's final place (`labelGenerator.createLabel`, `binPlacement` shift).

The rebuild dialog is fine today: changing a centered bin's base unit there makes a full rebuild
(`binCell.parameterEditKeepsPlacement`, review round 38), which centers it again.

## Options

| | Way | For | Against |
|---|---|---|---|
| **A** | The `Bin placement` move and the offsets after it take the centered offset as an **expression** of the bin's parameters, `(0.5 mm − 2 * gfBin1_baseWidth) / 2` | No new feature, the user sees the same timeline. Same `Dim` way the bin's geometry and joint origins already follow parameters (round 15, 46). Small, upstream has the same `Dim`, `moveBodies` and `footCenters` | Old bins keep their number until rebuilt |
| B | Build the bin around the origin (all sketches from −w/2) | No move at all | Touches every sketch of the bin, base, lip, label; far too big for a patch |
| C | A joint or the component's transform | – | A transform can't hold an expression; a joint to the origin is a new feature the user sees, and part designs build into the root |

## Decision (proposed)

Decided: **A**. A centered bin's offset is a `Dim` built from the bin's base unit parameters:

- X: `(2 × clearance − binWidth × gfBinN_baseWidth) / 2`, Y likewise with `binLength` and `gfBinN_baseLength`.
  `binWidth`/`binLength` are the bin's size in units as today (1.5 in a half grid; a custom shape is centered on its
  bounding rectangle as today). The clearance stays a number, as everywhere in the bin.
- The `Bin placement` move takes it through `dim.valueInput` (expression for a centered bin, number otherwise). The
  foot joint origins, pocket joint origins and colored label letters get the same `Dim`, so they follow too.
- Snapped (free spot), kept (rebuild in place of a snapped bin) and cell bins are unchanged: their offset stays a number
  (a cell bin has no move at all).
- Values at build time are the same as today to the 1e-6 mm, so existing snapshots don't change.

## What stays as it is

- **Rebuild dialog:** a base unit change on a centered bin still rebuilds the bin (`parameterEditKeepsPlacement`
  unchanged). That is correct for new and for old bins alike. Allowing a plain parameter edit for new centered bins
  would need telling old bins (number in the move) from new ones (expression); left out of the patch.
- **Bins saved before 1.2.1:** their `Bin placement` keeps its number, a change in the parameter table still leaves
  them off center. Any rebuild through the dialog (also OK without a change, if the dialog rebuilds then; else any
  setting change) builds them with the expression. They load and rebuild as before, no settings change. This goes into
  the CHANGELOG.
- Nothing new for the user to see: no extra timeline feature, the move just shows a formula instead of a number.
- Not in this round: the label command's inserts, baseplates and boxes (they have no Center on origin), snapping
  bins again after a size change.

## Tests

- pytest: `centeredPlacement` gives `Dim`s whose value equals today's numbers and whose expression names the bin's
  parameters (full grid, half grid 1.5 units, different width and length units); `placementUtils.moveBodies` hands a
  `Dim` expression to Fusion as a string, numbers as before; source checks that the foot and pocket joint origins and
  the label get the placement `Dim`s, and that snapped/kept placements stay numbers.
- Snapshot case `bin_2x1x3_centered_params_base_50x46`: 2×1×3 centered, joint origins on, base width 50 mm and base
  length 46 mm set after the build; the run compares it with the bin built with those values from the start (bodies
  and, by the bounding box, its place). Plus the affected existing cases: `bin_2x1x3_centered_joint_origins` and one
  snapped params case (`bin_1x1x3_params_base_40x50`) unchanged.
- Fusion script: centered 2×1×3 with a Cullenect socket and a colored label, base width 42 → 50 mm in the parameter
  table: bounding box symmetric about the origin (±0.01 mm), foot joint origins at ±25 mm, pocket joint origin and the
  colored letters moved with the tab; all sketches fully constrained.

## End-to-end criterion

In Fusion: a centered 2×1×3 bin, `gfBin1_baseWidth` 42 → 50 mm in the parameter table: the bin spans −49.75 … +49.75
mm in X, its foot joint origins sit at −25 and +25 mm; length 42 → 46 mm likewise in Y. A snapped bin beside it
keeps its left edge as before.
