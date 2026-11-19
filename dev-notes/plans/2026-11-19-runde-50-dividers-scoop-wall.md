# Round 50 plan – raised dividers on their grid lines beside a scoop wall (p650)

Spec: `dev-notes/specs/2026-11-19-runde-50-dividers-scoop-wall.md` (decision 2026-11-19). The plan of 93646f9
rested on a wrong finding and is replaced by this one.

1. **Tests first (pytest), `tests/test_scoop_sides.py`.** Pure functions in `lib/gridfinityUtils/scoopSides.py`,
   on numbers and Dims alike:
   - `gridTrims(walls, wall, scoopInset, keepGrid)` → (grid insets per side, trim per side): without `keepGrid` the
     grid insets are today's `wallInsets` and no trims; with it the grid insets are the wall on every side and the
     trim is `scoopInset − wall` on scoop walls.
   - `trimmedCavity(x, y, width, length, position, size, counts, trims)` → the cavity of a compartment from its grid
     cell: trimmed on the sides it touches.
   - `trimsKeepAlike(trims, counts)` → whether patterned compartments stay alike.
   Red, then code.
2. **Code, `binBodyGenerator.py`.** `keepGrid = input.hasLip and len(input.raisedDividers) > 0`. Grid from the grid
   insets; `compartmentPlacement` returns the trimmed cavity; `useCompartmentPattern` also needs `trimsKeepAlike`;
   compartments top clearance from the cavity bounds (today's `compartmentInsets`); `raisedDividerCorners` moves the
   corners of the outer cells by the trims. Raised divider boxes, tab openings and the lip bottom chamfer stay on
   today's values. Code comments: root cause, rejected options.
3. **Shape cases** (spec) with `settings.json`, e2e README.
4. **Fusion (slot via main session).** Diagnosis script: the three new cases and the 1U variant, divider positions,
   junction pictures, chain log; then snapshot runs: store the new cases, check
   `bin_3x2x3_dividers_to_top_3_columns_tab_scoop_part`, `bin_3x2x3_dividers_to_top_3_columns`,
   `bin_3x2x3_dividers_to_top_3_columns_lip_full`, `bin_4x2x3_cullenect_mixed_dividers_to_top` and the round 48 cases
   `bin_3x1x6_scoops_per_compartment`, `bin_2x2x4_scoops_4_lip_full_compartments` (all expected unchanged). Before and
   after pictures of the reported bin for the click test.
5. **CHANGELOG** `## Unreleased` → `### Raised dividers beside a scoop wall`; click test checklist
   `dev-notes/klicktest-r50.md`; docs page of the compartments if it describes scoop walls and the grid.
6. **Review** by an Opus subagent, findings fixed; merge master (8373140), pytest; PR text to the main session, push,
   PR, CI.

# Plan of the extension: lip profile on raised dividers

Spec section "Extension". Built after the open questions are decided; Option 1 above stays its own commit.

7. **Tests first (pytest), pure:** ridge half widths per lip type and trim from the lip constants (2.85/2.15 mm,
   crest 0.85 mm trimmed), support depth and reach into the compartment (3.45/2.25 mm Full, 0.85/1.55 mm Light with a
   1.2 mm wall), a wall thicker than the ridge needs no support; the tab and socket offset in front of a ridge and the
   scoop trim at a divider face as decided in Q1/Q2; the 1U rule of Q3.
8. **Code:** `createRaisedDividers` makes boxes as wide as the ridge base, cut by the stacked foot cutters as today;
   supports (Full) or chamfers (Light) per compartment along its cavity outline next to raised dividers, like
   `createLipSupport`; p83 corner rounding limited or dropped as measured; tabs, sockets and scoops per Q1/Q2.
9. **Fusion:** stacking script on the new contour (no overlap, ridge 0.25 mm from the feet), pictures of junctions
   and crossings, ledge check; all raised divider snapshot cases stored anew after a look (Q5), the scoop and tab
   cases re-checked; before and after pictures for the click test.
10. **Docs, CHANGELOG, click test, review, PR** as steps 5 and 6.

# Plan of the change to the divider's top (2026-11-19)

Replaces the ridge with the lip's whole profile, see the spec's last part.

1. `raisedDividers.dividerTop` (pure, tested): roof under an untrimmed lip, chamfered flat top under a trimmed one;
   `ridgeBox`, `ridgeTipDepth`, `coveredCornerRadius`, `cornerRadiusBetween`, `tipCornersBesideRidge`, `raisedSides`,
   `tabTopRise` and their tests go.
2. `createRaisedDividers`: per segment the divider's section sketched across its run (`raisedDividerWall`), extruded
   over it, cut by the stacked feet. The compartments are plain again: no ridge corner radii, no corner fills, no
   shorter compartment at a scoop on a divider; tab and label as on master.
3. p83 back: `FilletCorner`, `filletCorners`, the 3D chain (`isCornerEdge`, `chainPath`, `chainRuns`, `runOffset`
   in 3D with exact joins), `supportCornerPath` for the corner beside a full lip's support, all tested pure; the sweep
   in `roundRaisedDividerCorners`, section at the start of the chain, support path sketched in the divider face's
   plane from the grid's dims.
4. Fusion: snapshots of all cases with raised dividers stored anew after a look, the gap check over all 30 bin cases
   with compartments, stacked bins Full and Light, trimmed and not.
