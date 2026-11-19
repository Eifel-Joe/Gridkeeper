# Round 50 – raised dividers off their grid lines beside a scoop wall (p650)

Status 2026-11-19. Point p650 "Bin: dividers up to the top and lip give faulty geometry at the wall" (bug).
Branch `r50-dividers-lip` from `master` 5a9d4fa.

## Finding

Reproduced in Fusion by script: bin 2×3×5, hollow, 1.2 mm wall, lip Full, trimmed, compartments 2×3 with a front
scoop in every compartment, dividers up to the top on grid lines. Variants compared by pictures of the junctions and
by the logged positions of the raised dividers (body coordinates, the first grid line at y = 41.75 mm):

| Case | Lip | Scoops | Code | Divider across y | Off the grid line | Junction |
|---|---|---|---|---|---|---|
| A (reported) | Full | front in every compartment | master 5a9d4fa | 42.36–43.56 | 1.21 mm | narrow ridge, steps, gaps |
| I | Full | front only in the compartments on the front wall | master | 42.36–43.56 | 1.21 mm | same as A |
| H | Full | bin front scoop | fa10e31 (before rounds 46 and 48) | 42.36–43.56 | 1.21 mm | same as A |
| C | Light | front in every compartment | master | 41.90–43.10 | 0.75 mm | mostly fine, small sliver |
| B | Full | none | master | 41.43–42.63 | 0.28 mm | clean |
| E | Light | none | master | 41.43–42.63 | 0.28 mm | clean |

**Root cause.** A wall with a scoop starts the cavities at the lip's inner edge, for every compartment along it so
the compartment grid stays even (`scoopSides.outerScoopWalls`, round 48; before round 48 the same for the bin's front
scoop). The even grid is then shifted by `(lip inner inset − wall) × (count − line) / count`: with a full lip
(inset 2.6 mm) and a 1.2 mm wall the first of three rows' divider moves 0.93 mm further off, 1.21 mm in all. The
raised part of the divider is cut by the feet of a bin stacked on top (`createStackedFootCutters`), whose groove lies
on the grid line, so most of the shifted divider is cut away on one side: a narrow ridge, steps where the corner
rounding (p83) runs up a ridge that isn't there, gaps. Scoops on the divider faces play no part (case I), the
joint origins (round 46) neither. It is no regression: the bin front scoop did the same before round 48 (case H);
round 48 made it reachable through compartment scoops and on all four walls. A light lip is affected too, less
(inset 1.9 mm).

A first hypothesis, the full lip's support under the corner rounding, was wrong: case B with a full lip and no scoops
is clean. A fix built on it (rounding started lower) changed nothing of the fault and was dropped.

## Decision (2026-11-19)

Decided: with dividers up to the top the inner compartment grid stays on the grid lines, the inset of a scoop wall is
taken by the outer row or column only. Rejected: a scoop that stops at the wall under raised dividers (a step at the
top of the scoop, a change from round 48), and a raised part set on the grid line over a shifted divider (an offset of
up to 1.2 mm in the divider).

## Target geometry

For a bin with a lip and at least one raised divider (`input.raisedDividers`), and only there:

- The compartment grid (start, pitch) is laid out from the plain walls, as without any scoop: every divider lies
  where it lies in the same bin without scoops (0.28 mm off with a 1.2 mm wall, as today).
- A compartment along a scoop wall (`outerScoopWalls`, also the bin's front scoop) has its cavity start at the lip's
  inner edge on that side, as today: it is shorter by `lip inner inset − wall` (1.4 mm with a full lip and a 1.2 mm
  wall, 0.7 mm with a light lip). Compartments not along that wall keep the full pitch.
- Everything placed from a compartment follows its cavity: tab and label (back wall), Cullenect socket, the corners
  rounded by p83 at a scoop wall, the compartments top clearance (spans the cavities, from the scoop insets).
- Compartments are patterned only while they stay alike: a trim on a side every compartment touches (one row or one
  column along that axis) keeps them alike, any other trim builds each compartment on its own.

Bins without raised dividers keep the even grid of round 48 unchanged.

## Tests

- pytest (pure, numbers and Dims), `tests/test_scoop_sides.py`: the grid insets and trims per side
  (`gridTrims`), the cavity of a compartment from its cell (`trimmedCavity`), the corners of cells along a trimmed
  wall (`cornerTrim`), the start and end of a raised divider run at a trimmed wall (`runTrims`), when compartments
  stay alike for the pattern (`trimsKeepAlike`).
- New shape cases, compartments 1×3 so no dividers cross (see below):
  `bin_2x3x5_dividers_to_top_lip_full_compartment_scoops` (front scoop in every compartment as reported),
  `bin_2x3x5_dividers_to_top_lip_full_scoop` (the bin's front scoop), `bin_2x3x5_dividers_to_top_compartment_scoops`
  (light lip, right scoops: the trim across x). All pass, sketches fully constrained, no ledge.
- Unchanged in Fusion: `bin_3x2x3_dividers_to_top_3_columns_tab_scoop_part`, `bin_3x2x3_dividers_to_top_3_columns`,
  `bin_3x2x3_dividers_to_top_3_columns_lip_full`, `bin_4x2x3_cullenect_mixed_dividers_to_top`,
  `bin_3x1x6_scoops_per_compartment`, `bin_2x2x4_scoops_4_lip_full_compartments`.
- The reported bin rebuilt: the dividers lie at y 41.43–42.63 mm as without scoops, the junctions are clean.

## Found on the way, not changed (points p651–p653)

- Where raised dividers cross (2×3 compartments), four corners get no rounding and leave level faces of 0.05 mm²,
  with or without scoops, on master too. The ledge check of the shape tests reports them, so the new cases have
  no crossings.
- A bin one height unit high with a scoop fails at its compartments' bottom fillet, on master too; without a scoop
  the same bin with a full lip and dividers up to the top builds clean.
- In the bin corner between two scoop walls (front and left) a level face of 1.11 mm² is left at the top with
  dividers up to the top, on master too.

## Implementation notes

- A raised divider at a trimmed scoop wall starts half a wall short of the trimmed cavity, as before: started from
  the grid it reached out under the lip, with faces nearly coincident with the lip's, an extra ledge and a changed
  `…_tab_scoop_part` case (shown in Fusion, dropped).

# Extension: the lip's profile on both sides of a raised divider

## Decision (2026-11-19)

Decided: the top of every raised divider gets the lip's profile on both sides, mirrored towards both compartments,
so the feet of a bin stacked on top sit in the groove between them the way they sit at the outer wall. This replaces
the flat top of round 8 (p61), and is part of round 50.

## What the feet of a stacked bin need, measured in Fusion

Two equal bins 2×2×3 with 2×2 compartments and dividers up to the top, the upper one raised by 3 × 7 mm, cut across
the grid line y = 42 mm in the middle of a compartment (`fusion-auftraege/r50_stack.py`). Heights from the lower bin's
body top (= lip bottom), distances from the grid line; 0.25 mm clearance, 1.2 mm wall, lip top trimmed:

| | Full lip | Light lip |
|---|---|---|
| Overlap of the two bins today | 0 mm³ | 0 mm³ |
| Groove between two feet over the grid line, half width | 3.2 mm at 0, 2.4 mm from 0.8 to 2.6 mm, 0 at 5.0 mm | the same (the feet don't depend on the lip type) |
| Lip at the outer wall, from the grid line | tip 2.85 mm at 0 to 0.7 mm, 45° in to 2.15 mm, straight to 2.5 mm, 45° out to 0.85 mm at the top (3.8 mm, trimmed) | 45° from the wall face 1.45 mm at 0 to 2.15 mm at 0.7 mm, straight to 2.5 mm, 45° to 0.85 mm at the top |
| Under the lip | support: straight down 1.2 mm from the tip, then 45° into the wall | nothing, the chamfer above starts at the wall face |

The lip keeps 0.25 mm to the feet everywhere (2.15 mm against 2.4 mm, 2.85 mm against 3.2 mm).

## Target contour

The ridge on a grid line is the lip's inner profile mirrored about the grid line, at the same clearance to the feet:
in effect the groove between two feet less the clearance. It is made the way the raised dividers are cut today, by
the feet of a bin stacked on top with clearance (`createStackedFootCutters`, Full with the socket's bottom chamfer),
from a box as wide as the groove instead of the divider. So:

1. **Profile by lip type.**
   - Full: 5.7 mm wide at the body top (half 2.85 mm), 45° in to 4.3 mm, straight, 45° to a 1.7 mm crest at the trimmed
     top. Under it a support like the outer lip's: straight down 1.2 mm from both tips, then 45° into the divider. With a
     1.2 mm divider that reaches 3.45 mm under the body top and 2.25 mm into each compartment.
   - Light: 4.3 mm wide (half 2.15 mm) from 0.7 mm over the body top, 45° to the crest. Under it the light lip's
     chamfer mirrored, 45° from the divider face, reaching 0.85 mm under the body top and 1.55 mm into each
     compartment.
   - Lip off: no raised dividers (the option needs a lip), unchanged.
2. **Wall and crossings.** The ridge and the outer lip are cut by the same feet, so their faces run into each other at
   the wall. Where they meet, and where two ridges cross, the rounded corners of the feet (bin corner radius 4 mm plus
   clearance) round the concave corners. Under the ridge the supports or chamfers meet the outer wall's at a sharp
   concave corner unless they are built per compartment, along its cavity outline like the outer support: the plan
   builds them that way. The rounding of the divider corners of p83 is then no longer needed above the support and is
   dropped for raised dividers with this contour (to be confirmed in Fusion: no ledge, no sharp corner).
3. **Trim lip top.** The ridge follows the lip's top: trimmed, a 1.7 mm flat crest at the lip's trimmed height;
   untrimmed, up to the lip's full height with a crest of about 0.5 mm.
4. **Label tab, scoops, Cullenect.**
   - The ridge and its support reach 2.25 mm (Full) or 1.55 mm (Light) into each compartment at the body top, more
     than the outer lip's tip (1.4 mm with a 1.2 mm wall).
   - A label tab at the back of a compartment in front of a raised divider lies under the ridge like a tab at the
     back wall lies under the lip; the ridge covers its back 2.25 mm instead of 1.4 mm.
   - A Cullenect socket in such a tab: at the back wall it already clears the support by only about 0.05 mm (point of
     the upstream round, Fund 4); under a ridge its back 0.85 mm more would be covered and the insert wouldn't go in.
   - A compartment scoop on a divider face: the support meets the top of the scoop like the outer support meets a
     wall; at an outer scoop wall the cavity instead starts at the lip's inner edge.
5. **Evidence:** see the table; the current raised dividers already never collide with a stacked bin, the ridge only
   fills the groove up to the clearance.

## Decisions on the open questions (2026-11-19)

- Q1 decided: a label tab and its Cullenect socket in front of a raised divider start at the ridge's tip.
- Q2 decided: a compartment scoop on a divider face is built as at an outer scoop wall: the compartment starts at the
  ridge's tip on that side, the scoop runs up without a step.
- Q3 decided: in a bin one height unit high the support is cut off at the compartment floor like the outer one.
- Q4, Q5 decided: the extra material and the ridge on rebuilt saved bins are accepted; the snapshot cases with raised
  dividers are stored anew after a look.

## Details settled while building

- The ridge is centred on the grid line, where the groove between the feet is; the divider is not (its faces lie
  0.32 mm and 0.88 mm off the grid line with a 1.2 mm wall, as since round 8). The support (Full) or chamfer (Light)
  under each side runs at 45° from the ridge's tip to that side's divider face, so the two sides differ a little.
- With the ridge the rounding of the divider corners (p83) is not built: above the support the feet's rounded corners
  shape the ridge where it meets the lip or another ridge; below, the compartment's corner fillet meets the support
  as at the outer wall. Where a ridge's support meets the outer support or another ridge's, the concave corner stays
  sharp (45° faces, printable).

## Open questions as asked (answered above)

- **Q1 Tabs and Cullenect sockets under a ridge:** (a, recommended) a tab and its socket in front of a raised divider
  start at the ridge's tip, as far in as its overhang (the label face keeps its width, the compartment loses the
  overhang at the top only); (b) the ridge is narrowed where a tab is (the feet then sit unguided there); (c) leave
  it, the socket can't take an insert under a ridge.
- **Q2 Compartment scoop on a divider face:** (a, recommended) as at an outer scoop wall: the scoop runs up to the
  ridge's tip without a support step, the compartment is shorter by the overhang on that side; (b) the support stands
  above the scoop like at a plain wall.
- **Q3 Bins one height unit high:** the cavity is about 1 mm deep, the Full support needs 3.45 mm: (a, recommended)
  the support is cut off at the floor like the outer one, the ridge stands on a solid band along the divider; (b) no
  ridge in 1U bins, the flat top as today.
- **Q4 Material:** under a full lip the ridge and support add about 18 mm³ per mm of divider (estimated from the
  section; a 2×3 bin with 2×3 compartments about 5 cm³), more print time; no question if accepted.
- **Q5 Existing bins:** every saved bin with dividers up to the top rebuilds with the ridge; all snapshot cases with
  raised dividers change and are stored anew after a look.

## Corners beside a ridge (decided 2026-11-19, option a)

Measured on the reported bin with the ridge: where a raised divider meets the outer wall a level face of 0.10 mm²
(0.27 × 1.15 mm) is left 0.5 mm under the body top. The compartment's vertical corner fillet (2.55 mm with a 1.2 mm
wall) reaches past what covers it from above, the ridge's tip on one side (only 1.97 mm from the divider face, the
divider lying 0.28 mm off the grid line), and the compartments top clearance cuts it flat. The rounding of p83
covered it before; it doesn't fit the ridge. Rejected: accepting the faces (a weaker ledge check), supports built
along every compartment's outline (much more work and risk).

Decided: a compartment corner next to a ridge gets a smaller fillet, so that it lies wholly under what covers it.
Each side of the corner covers a strip from its face, measured at the height where the cavity's top is cut (the tab
top offset, or the body top without one): a ridge its overhang there (Full: tip − face distance; Light: tip − face
distance − that depth), an outer wall under a full lip its support (lip inner inset − wall), anything else nothing.
Two strips a and b cover a corner fillet of radius r when r ≤ min(a, b) or (r − a)² + (r − b)² ≤ r², so
r = min(corner radius, a + b + √(2ab)). Corners away from ridges keep their radius. A corner with nothing to cover it
stays sharp.
Settled in Fusion: a compartment beside a ridge takes the tightest of these radii at all four corners and for its
floor fillet. Corners of different radii broke the floor's outline beside a scoop into edges Fusion found no fillet
for (`FILLET_NO_EDGE_FOUND`, also with the floor fillet at the tightest radius); with one radius per compartment, as
before, every cavity builds. The reported bin: 2.25 mm beside a ridge, 1.40 mm where a compartment scoop starts the
cavity at the ridge's tip, no ledge left.
This goes beyond the decision, which concerned the corners beside a ridge only: it follows from that limit of Fusion
(two attempts with a radius per corner failed), so a compartment beside a ridge has all its corners and its floor
fillet at the tightest radius.

# Points p651–p653 (taken into round 50, 2026-11-19)

## p651 Tiny ledges where raised dividers cross

Cause: at a crossing the compartment corners were not rounded up by p83 (no chain of edges there), the compartments
top clearance cut their corner fillets flat, 0.05 mm² each. Target: with the ridges both sides of such a corner are
ridges, their overhang (at least 1.97 mm) covers the fillet; the corner rule above keeps it so. Check: the reported
bin (2×3 compartments) has no ledge at its crossings; a new shape case with crossing ridges.

## p652 A bin one height unit high with a scoop doesn't build

Cause, shown in Fusion with a 2×3×1 bin with a front scoop and no dividers: the cavity is 1.0 mm deep, its scoop and
corner fillets are built (2.55 mm), then the bottom fillet of 2.55 mm along the other walls fails
(`ASM_BL_CAP_COMPLEX`). Without the scoop the same bottom fillet builds. Limiting the scoop to the depth instead makes
the corner fillets fail (`ASM_BL_CANNOT_REORDER`); limiting the bottom fillet to the depth less 0.1 mm builds.
Target: the bottom fillet of a cavity with a scoop is at most its depth less the scoop's top margin (0.1 mm); scoop and
corners unchanged, cavities without a scoop unchanged. Check: new shape case 2×3×1 with a front scoop.

## p653 Ledge in the corner between two scoop walls

Cause: where two walls with a scoop meet (front and left), the cavity starts at the lip's inner edge on both, but its
corner fillet keeps the compartment radius (2.55 mm) while the lip's inner corner there is concentric with the bin's
(4.0 mm less the inset: 1.4 mm under a full lip, 2.1 mm under a light one); the top of the fillet is left as a level
face of 1.11 mm² at the body top, with or without raised dividers. Target: a cavity corner between two scoop walls is
concentric with the lip's inner corner, radius bin corner radius less the scoop inset. Shape cases with two adjacent
scoop walls from round 48 change and are stored anew after a look. Check: new shape case with front and left scoops
and dividers up to the top.
