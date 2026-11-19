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
