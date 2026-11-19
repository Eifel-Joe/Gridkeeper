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

## Decided

- Scoops are chosen per wall, four checkboxes (front, back, left, right). The wall carrying the label tab (the back
  wall) is locked while the tab is on, so at most three with a tab.
- Compartments: scoops follow the same rule as today's single scoop, only on more walls.
- Today's bin with one front scoop stays the same in geometry and in its saved settings.
- (addendum) The back wall is locked only while a label tab is chosen; without a tab up to four scoops, also per
  compartment.
- (addendum) Per compartment: the compartment layout editor can choose the scoop walls of each compartment; a
  compartment without a choice of its own takes the bin's four checkboxes. Old configs load unchanged.
- (addendum) The scoop radius may be limited where needed (several scoops, small compartments), automatically from
  the compartment's size; `Scoop max radius` stays the upper bound.

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

## Scoops per compartment (addendum)

- Data: a compartment pocket (`compartmentLayout.pocket`) gets `scoops`: `None` = like the bin (default, also for
  every pocket of an old config), or a list of walls (`[]` = none). `_sanitized` keeps only known wall names,
  anything else becomes `None`. `isCustomized` counts a pocket with its own scoops; `isUniform` is false then (the
  pattern copies one cavity, it can't vary), `describe` names them.
- Walls of a compartment are its own four walls (its front is the bin's front wall or a divider). Decided by the
  addendum: the tab wall is locked for every compartment while a tab is chosen, since every compartment carries its
  own tab on its back wall. `scoopSides.compartmentScoopSides(pocketScoops, binSides, hasTab)`.
- Generator: `BinBodyCompartmentDefinition.scoopSides` per compartment, the cutter takes the compartment's. The outer
  bounds (lip inner edge) and the lip bottom chamfer follow the bin walls where **any** compartment along that wall
  has a scoop on it (`scoopSides.outerScoopWalls`), so the compartment grid stays even; creases skip those walls.
- Editor (`html/compartments.html`): the selected compartment's panel gets a row **Scoops** with a choice
  `Like the bin` / `Own` and four toggles Front, Back, Left, Right (Back disabled while a tab is chosen); merge keeps
  the source pocket's choice, split gives every cell the pocket's choice. A compartment with own scoops shows a small
  mark in the drawing. The data sent to the page gets `binScoops` (the bin's walls) for `Like the bin`.
- Saved with the pockets in the config and the recorded defaults, so Load, rebuild and clone carry them as they carry
  depth and label today.

## Radius limit (addendum)

The scoop radius of a compartment is `min(Scoop max radius, depth - top margin)` at least the corner fillet, as
today, and additionally, on an axis with scoops on **both** walls, at most half the compartment's span on that axis
less `BIN_SCOOP_FLOOR_MARGIN` (new, 0.5 mm), so a flat strip of floor stays between them. An axis with one scoop
keeps today's limit, so today's bins with one scoop are unchanged. One radius for all scoops of a compartment (one
fillet feature).

## Bottom fillet with several scoops (found in Fusion, 19.11.)

The cavity's bottom fillet fails (`FILLET_NO_EDGE_FOUND`) whenever its floor chain runs into two different scoops,
with or without the tangent chain: front+back, front+left+right and front+left failed, front alone and left alone
build. Every pick of two or more scoops has such a chain, so a compartment with more than one scoop gets no bottom
fillet, its floor edges at the plain walls stay sharp (`scoopSides.bottomFilletSides`).

## Dialog

Group **Scoop**: `Front (along bin width)` (the old `Add scoop (along bin width)` input), `Back (along bin width)`,
`Left (along bin length)`, `Right (along bin length)`, then `Scoop max radius (mm)`, enabled when any side is on.
`Back` is disabled while the label tab is on (tooltip says why), its value stays. Shaped bins: all disabled as today.

## Not part of this round

- Scoops for shelled, solid or shaped bins.
- A label tab on another wall than the back.
- Per-side radii (one radius per compartment, limited automatically).
- Scoops in other places than walls of a compartment (e.g. only part of a wall).

## Done when (end to end)

- pytest green, new unit tests for `scoopSides`, crease sides, config older values.
- Snapshot cases, new: `bin_3x1x4_scoops_front_back` (2), `bin_2x2x4_scoops_3_tab` (3, front+left+right, tab, light
  lip), `bin_2x2x4_scoops_4_lip_full_compartments` (4, full lip, 2x2 compartments). Unchanged fingerprints of the
  existing scoop cases (`bin_2x2x4_scoop_radius_10`, `bin_2x2x4_lip_full_scoop_tab`, `bin_2x1x3_wall_3_scoop_compartments`,
  `bin_3x2x3_dividers_to_top_3_columns_tab_scoop_part`, `bin_2x3x5_features`). Every sketch fully constrained.
- Snapshot case for per-compartment scoops and the radius limit: `bin_3x1x6_scoops_per_compartment` (3 compartments
  along X: left one Front+Left, middle `[]`, right Like the bin with Front+Back+Right and no tab, radius limited on Y).
- Click test in the dialog (`dev-notes/klicktest-r48.md`) including the editor, docs page
  `docs/bins/compartments.md` with new pictures (bin with 2/3/4 scoops, editor with per-compartment scoops).
