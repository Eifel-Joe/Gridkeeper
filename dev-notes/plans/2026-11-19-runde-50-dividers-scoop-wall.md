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
