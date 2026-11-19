# Round 46: joint origins of bins, baseplates and inserts without a sketch each

Point: p590 "Gelenkursprünge von Bin, Baseplate und Einleger ohne eigene Skizze" (improvement).

## Today (master fa10e31)

`baseGenerator.createPointJointOrigins` makes every joint origin of a bin, a baseplate and a Cullenect insert: per
point a sketch (a construction plane per height), a sketch point and two driving distance dimensions, the joint origin on
that point. Round 45 measured 846 ms and 8 model parameters per joint origin this way against 160 ms and 4 for a joint
origin on the component's origin point with offsets X, Y, Z (`jointOriginLayout.createOffsetJointOrigins`, used by the
box since round 45; `fusion-auftraege/r45_probe.log`).

Callers left on the sketch way:

| Where | Joint origins | Count |
|---|---|---|
| `baseGenerator.createCellJointOrigins` ← `baseplateBuilder` | `Socket joint origin c-r` | one per cell, 36 for 6×6 |
| `baseGenerator.createCellJointOrigins` ← `binBuilder._buildBin` | `Foot joint origin c-r` | one per foot (half grid: per half cell) |
| `binBuilder._buildBin` | `Pocket joint origin …` (Cullenect pockets, tagged with the pocket size) | one per pocket |
| `binBuilder._buildBin` | `Cell placement joint origin` (bin built into a cell) | 0 or 1 |
| `labelBuilder` | `Insert joint origin` | 1 |

## Requirement (from the point)

Same place, axes and parameter behaviour as today; joints work unchanged (bin in cell, insert in pocket, snap to free
spot, rebuild repointing, box label); documents with old joint origins stay valid, a rebuild makes the new kind. Measured
before/after: baseplate 6×6, bin, insert; build and rebuild.

## Decision

- `createCellJointOrigins` builds through `jointOriginLayout.createOffsetJointOrigins` (same points, names, order, z
  `-BIN_BASE_HEIGHT`, same return). The bin's pocket and cell placement joint origins and the insert's joint origin call
  `createOffsetJointOrigins` directly with the points they pass today.
- `createPointJointOrigins` has no caller left afterwards and is removed (with its plane-per-height cache). Its docstring
  history (unsigned dims, over-constraint with shared points) moves into one sentence of `createOffsetJointOrigins`'
  docstring as the reason that way is gone.
- Offsets are signed, so the `abs` workaround of the distance dimensions falls away; a point left of or below the origin
  sits where it did (the sketch point was placed at the signed spot, the dimension only held the magnitude).
- Parameter behaviour: the offsets get the same dims through `valueInput` as the dimensions got through `applyTo`: an
  expression where the dim hangs on a parameter (`gfBaseplate1_baseWidth`, `gfBin1_baseWidth`, the insert's width), a
  number otherwise. Round 45 showed `baseWidth` changes move offset joint origins like sketch ones.
- Body placement: like the sketches, offsets don't follow moves of bodies; the callers already pass the spots after the
  placement (comments saying "sketches which don't follow body moves" get the new wording).
- Old documents: nothing migrates. A joint origin on a sketch point stays valid where it is. A rebuild deletes the old
  timeline group with its sketches and planes (`rebuildUtils`, unchanged) and builds the new kind; joints on the old
  ones move over by name as today (R36, R43). Code that reads a joint origin's place goes through `jointOriginPlace`
  (round 45 guard test), which reads both kinds correctly.
- Bins and baseplates refuse direct designs already; an insert has no parameters there, its offsets are numbers.

### Kept as is
Names, order, the pocket tags, the `hasJointOrigins` and preview guards, the timeline groups, the joints and their names,
`binCell.cellOf` (names only).

## Expected
Per joint origin about 0.7 s less and 4 fewer model parameters: baseplate 6×6 about 36 × 0.7 ≈ 25 s less on build and on
rebuild, 144 fewer parameters and 36 sketches + 1 plane fewer; a 2×1 bin with one pocket 3 joint origins (≈ 2 s); an
insert 1 (≈ 0.7 s). Every later feature in the document gets cheaper by the fewer parameters (round 39). Measured, not
promised.

## Measured (Fusion, 19.11.2026, `fusion-auftraege/r46_mess.py`, log `r46_mess.log`)

Each run in a new hybrid document; base = master fa10e31, branch = this round; "migrate": base builds, branch rebuilds.

| Step | base | branch | migrate (rebuild by branch) |
|---|---|---|---|
| Baseplate 6×6 build | 9.7 s, +294 parameters, 36 sketches, 1 plane | 5.6 s, +220, none | – |
| Bin 2×1×3 Cullenect in socket 2-2 | 9.5 s, +178, 4 sketches, 3 planes | 7.4 s, +164, none | – |
| Insert in the pocket | 3.5 s, +56 | 2.9 s, +52 | – |
| Baseplate rebuild (Light) | 27.7 s | 12.0 s | 13.3 s, old sketches gone |
| Bin rebuild (height 4, no lip) | 11.4 s | 8.3 s | 9.1 s |
| Insert rebuild | 3.5 s | 2.3 s | 2.8 s |
| `gfPlate1_baseWidth` 42 → 50 mm | socket 2-2 +12 mm, bin follows | same | same |

Every step: bin in socket 2-2, insert mid floor of its pocket, timeline and joints healthy, every sketch fully
constrained. Snapshot cases (`r46_snap.log`): baseplate_2x2_light_params_base_40x50, bin_2x1x3_cullenect_params_base_40,
bin_1x1x3_cullenect_params_length_50_height_10, label_1u_screw_text: pass.

## Not part of this round
- Other sketch uses in bins/baseplates (feet, sockets, magnets): their shape needs them.
- Box label (`predBoxLabel`), box insert, handle, latch joint origins: their own ways (a point on geometry), untouched.

## Tests
- pytest (TDD, red first):
  - `createCellJointOrigins` makes offset joint origins: with a stand-in component that has no sketches and no planes
    (as in `test_offset_joint_origins.py`), names `Foot joint origin 1-1 …`, offsets = cell centers, z `-BIN_BASE_HEIGHT`,
    an expression offset for a parameter-bound width.
  - Source checks: `binBuilder._buildBin` and `labelBuilder` call `createOffsetJointOrigins` and no longer
    `createPointJointOrigins`; `baseplateBuilder` keeps calling `createCellJointOrigins`; `createPointJointOrigins` is
    gone from the add-in (replaces `test_bins_baseplates_and_labels_keep_the_sketch_way`).
  - The round-45 guard (`geometry.origin` only of planes) stays green.
- Fusion e2e helpers that read bin/baseplate/insert joint origins by `geometry.origin` (`tests/e2e/runde13_assembly.py`,
  `runde15_grid.py`, `runde31_cells.py`) switch to the transform's translation, as `jointOriginPlace`.
- Fusion measurement `fusion-auftraege/r46_mess.py` (pattern `r45_mess.py`, one step per call, state file): base (master
  fa10e31 export) and branch, each in a new hybrid document: baseplate 6×6, bin 2×1×3 with Cullenect pocket into socket
  2-2, insert into its pocket; then rebuild of baseplate, bin and insert; `gfBaseplate1_baseWidth` 42 → 50 mm. Per step
  time, model parameter count, sketches and planes in the component, joints healthy (bin in cell, insert in pocket),
  bin follows the socket after the parameter change, every sketch fully constrained. A third run "migrate": base builds,
  branch rebuilds all three in the same document (old-kind joint origins replaced, joints still healthy).
- Snapshot cases (geometry unchanged, joint origins aren't in the fingerprint; timeline/parameter health):
  baseplate_2x2_light_params_base_40x50, bin_2x1x3_cullenect_params_base_40,
  bin_1x1x3_cullenect_params_length_50_height_10, one insert (label) case.
- Click test `dev-notes/klicktest-r46.md`: baseplate 6×6 from the dialog (no joint origin sketches, origins in the
  sockets), bin into a socket, insert into the bin's pocket, snap to free spot, rebuild each, parameter change, box with a
  bin in a cell and a box label (unchanged), an old document rebuilt.
