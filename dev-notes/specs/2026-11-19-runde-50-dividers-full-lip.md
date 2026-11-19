# Round 50 – raised dividers under a full lip (p650)

Status 2026-11-19. Point p650 "Bin: dividers up to the top and lip give faulty geometry at the wall" (bug).
Branch `r50-dividers-lip` from `master` 5a9d4fa.

## Finding

Reproduced in Fusion by script (bin 2×3×5, hollow, 1.2 mm wall, lip Full, trimmed, compartments 2×3, dividers up
to the top on grid lines). Variants, all built from the same code:

| Case | Lip | Compartment scoops | Code | Where a raised divider meets the outer wall |
|---|---|---|---|---|
| A | Full | front in every compartment | master 5a9d4fa | block with flat faces under the lip, one side sharp |
| B | Full | none | master 5a9d4fa | same as A |
| B | Full | none | fa10e31 (before rounds 46 and 48) | same, sharp corner with a sliver |
| E | Light | none | master 5a9d4fa | rounded from the compartment corner up to the top, as specified in round 8 (p83) |

So the trigger is the full lip together with dividers up to the top. Compartment scoops (round 48) and joint origins
(round 46) play no part, and it is no regression: `raisedDividers.py` and `binBodyLipGenerator.py` are unchanged since
fa10e31, the full lip came in with the upstream merge of 17.11.2026 (p13), whose review already flagged this corner
("Fund 2") for a look in Fusion.

**Root cause.** The rounding of a raised divider's corner (p83, `roundRaisedDividerCorners`) sweeps the section of the
compartment's corner fillet, drawn at the compartment corner at `bottomZ = top − tabTopOffset` (29.5 mm in the
case), along the edges of the corner in the divider's face from `bottomZ` up. Under a light lip that chain starts at
the compartment corner. A full lip has a support under its inner tip (`createLipSupport`, upstream): straight down
1.2 mm from the tip, then out at 45° into the wall, reaching 2.6 mm below the bin top with a 1.2 mm wall. At
`bottomZ` the cavity wall is the support's tip face, 1.4 mm in from the compartment corner. Logged chain of the corner
at the right wall, divider y = 41.43 mm (x, z in mm): `(80.9, 29.5)→(80.9, 30.0)→(81.6, 30.7)→(81.6, 32.5)→(82.9,
33.8)`, the compartment corner is at x = 82.3. The path starts 1.4 mm off the section, so the swept piece lands beside
the corner it should round; the support's faces stay sharp against the divider, and the compartment's corner fillet
below runs into them, hence the steps, blocks and slivers in the pictures.

## Target geometry (decided)

Under a full lip the corner of a raised divider is rounded the same way as under a light lip: one round of the
compartment's corner fillet radius, from the compartment corner up to the top of the lip, without a step. It starts
where the support's 45° face meets the wall's inner face (2.6 mm under the bin top with a 1.2 mm wall, i.e.
`lip support wall height + lip inner inset − wall thickness`, never above the old start `top − tabTopOffset`), and
follows the support's 45° face, its straight face under the tip, the lip socket's chamfer and faces up to the top.
The support itself stays as it is. This is the shape round 8 / p83 specified ("rounded from the top of the
compartment's corner fillet up to the top, over the outer wall, the chamfer under the lip and the lip"), the support
takes the place of the light lip's chamfer, so no previously approved behavior changes.

Light lips, bins without raised dividers and walls at least as thick as the full lip's inset (support inside the wall)
keep today's start.

## Not included

- Bins one height unit high under a full lip: the support is cut off at the floor there, the slope never reaches
  the wall face. Raised dividers in such a bin stay as they are; new point if it matters.
- The four "no edges found" messages at divider crossings: the same with a light lip, those corners are rounded by
  the neighbouring ones; unchanged.

## Tests

- pytest: the start depth of the corner rounding as a pure function (light lip, full lip with 1.2 mm wall, full lip
  with a wall thicker than the inset, tab top offset larger than the support).
- Snapshot check `raisedCornerLedgeNotes` looks down to the new start under a full lip (sister path).
- New shape case `bin_2x3x5_dividers_to_top_lip_full_compartment_scoops` (the reported bin) and
  `bin_2x3x5_dividers_to_top_lip_full` (2×3 compartments, no scoops). The only existing full-lip case with raised
  dividers, `bin_3x2x3_dividers_to_top_3_columns_lip_full`, is expected to change (its snapshot holds the faulty
  corners) and is updated after looking at it.
- Light-lip raised divider cases run unchanged: `bin_3x2x3_dividers_to_top_3_columns`,
  `bin_3x2x3_dividers_to_top_3_columns_lip_untrimmed`.
