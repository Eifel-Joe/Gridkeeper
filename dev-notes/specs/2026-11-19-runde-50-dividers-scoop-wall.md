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

- pytest (pure, numbers): the trims per side from the scoop walls and insets; the cavity placement of a compartment
  in a 2×3 grid with a front scoop wall, full and light lip; no trims without raised dividers; when compartments
  stay alike for the pattern.
- New shape cases: `bin_2x3x5_dividers_to_top_lip_full_compartment_scoops` (the reported bin),
  `bin_2x3x5_dividers_to_top_lip_full_scoop` (bin front scoop), `bin_2x3x5_dividers_to_top_compartment_scoops`
  (light lip). Bins one height unit high with a full lip, dividers up to the top and a scoop: checked in Fusion, a
  case of their own if they build, else a new point.
- Existing cases re-checked in Fusion: `bin_3x2x3_dividers_to_top_3_columns_tab_scoop_part` (front scoop, column
  dividers: expected unchanged, the trim is on a side every compartment touches), the raised divider cases without
  scoops (unchanged), the round 48 scoop cases without raised dividers (unchanged).
