# Round 48: more scoops (up to four)

Idea: teateatea, upstream issue Le0Michine/FusionGridfinityGenerator#140 ("[Feature Request] Multiple Scoops"):
two scoops for long parts rolled out along both long sides, four for small parts reached from every side, three when
one side carries the label tab. Upstream has no code for it.

## Today

One scoop on the front wall (min Y) of every compartment: `binBodyCutoutGenerator` fillets the bottom edge of the
cavity cutter's front face with `scoopMaxRadius` (clamped to the depth less `BIN_SCOOP_TOP_MARGIN`, at least the corner
fillet). Around it:

- With a lip, the compartments start at the lip's inner edge on the front (`compartmentsMinY = lipInnerInset`), so the
  scoop runs up into the lip without a step; the lip bottom chamfer box leaves the front out.
- The bottom fillet of the cavity starts at the back bottom edge (tangent chain).
- Wall creases skip the front wall (`skipFront`), the scoop braces it.
- Label tab: always on the back wall of each compartment.
- Shelled, solid and shaped bins build no scoop (unchanged).

## Requirement

- Scoops on any of the four walls: front, back, left, right, each switched on its own.
- The back scoop is not built while the label tab is on (the tab sits on the back wall), so at most three with a tab.
- A bin with today's front scoop only is built exactly as before (same snapshot fingerprints), and saved settings
  without the new fields load as before (no new scoop).

## Options

1. **One checkbox per wall** (chosen). The existing `hasScoop` stays the front scoop (same input ID, same config field);
   new fields `hasScoopBack`, `hasScoopLeft`, `hasScoopRight`, default off. Covers 2 (front+back or left+right),
   3 and 4 and any other pick.
2. A count dropdown 1–4 with fixed sides. Simpler to click, but "2" has to guess which pair is the long one and a bin
   turned in the grid needs the other pair; the per-side list is no harder to read.

## Design

- `scoopSides(state)` (pure, unit tested): the set of sides from the four flags; `back` dropped while the tab is on;
  empty for non-hollow or shaped bins. `BinBodyGeneratorInput`/`BinBodyCutoutGeneratorInput` get `scoopSides`
  instead of `hasScoop`.
- Cavity cutter: the bottom edges of all scoop side faces, picked before any fillet, are filleted in **one** fillet
  feature (rolling-ball corners blend two adjacent scoops), then the vertical corner fillets as today. The bottom fillet
  starts at the bottom edge of the first wall without a scoop in the order back, left, right, front (today's back edge
  for a front scoop); a wall whose edge is not in that tangent chain gets its edge added. Four scoops: no bottom fillet.
- Compartment bounds: every scoop side starts at the lip's inner edge (light and full lip) like the front today,
  `compartmentsMinX/MaxX/MinY/MaxY`. The compartments top clearance and the raised dividers use those bounds.
- Lip bottom chamfer box: inset to the lip's inner edge on every scoop side; the chamfer leaves out the top-face edges
  touching a scoop side (lines and their corner arcs), picked by position instead of today's `[3:]` slice. No edges
  left (four scoops): no chamfer, no cut.
- Compartments and dividers: every compartment gets the scoops of the chosen sides, as the front scoop does today
  (dividers get scooped on both faces where both neighbours scoop there).
- Wall creases: every scoop side is left out (`creaseLayout(..., scoopSides)` instead of `skipFront`).
- Cullenect sockets and hollow tabs stay on the back wall; a left or right scoop runs under the tab's ends, the tab is
  joined over it as today. No back scoop with a tab, so the socket never meets a scoop.

## Dialog

Group **Scoop**: `Front (along bin width)` (the old `Add scoop (along bin width)` input), `Back (along bin width)`,
`Left (along bin length)`, `Right (along bin length)`, then `Scoop max radius (mm)`, enabled when any side is on.
`Back` is disabled while the label tab is on (tooltip says why), its value stays. Shaped bins: all disabled as today.

## Not part of this round

- Scoops for shelled, solid or shaped bins.
- A label tab on another wall than the back.
- Per-side radii.

## Done when (end to end)

- pytest green, new unit tests for `scoopSides`, crease sides, config older values.
- Snapshot cases, new: `bin_3x1x4_scoops_front_back` (2), `bin_2x2x4_scoops_3_tab` (3, front+left+right, tab, light
  lip), `bin_2x2x4_scoops_4_lip_full_compartments` (4, full lip, 2x2 compartments). Unchanged fingerprints of the
  existing scoop cases (`bin_2x2x4_scoop_radius_10`, `bin_2x2x4_lip_full_scoop_tab`, `bin_2x1x3_wall_3_scoop_compartments`,
  `bin_3x2x3_dividers_to_top_3_columns_tab_scoop_part`, `bin_2x3x5_features`). Every sketch fully constrained.
- Click test in the dialog (`dev-notes/klicktest-r48.md`), docs page `docs/bins/compartments.md` with new pictures.
