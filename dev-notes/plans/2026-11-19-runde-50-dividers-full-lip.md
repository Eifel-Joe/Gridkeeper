# Round 50 plan – raised dividers under a full lip (p650)

Spec: `dev-notes/specs/2026-11-19-runde-50-dividers-full-lip.md`.

1. **Test first (pytest).** `tests/test_raised_dividers.py`: `raisedCornersDepth(tabTopOffset, hasLipSupport,
   lipInnerInset, wallThickness)` in `lib/gridfinityUtils/raisedDividers.py` (pure, cm): light lip → tab top offset;
   full lip, 1.2 mm wall, inset 2.596 mm → 2.596 + 1.2 − 1.2 = 2.596 mm; full lip, wall ≥ inset → tab top offset;
   tab top offset deeper than the support → tab top offset. `tests/test_test_cases.py`: `raisedDividersReach` takes
   that depth, so the ledge check looks below the new start. Red, then code.
2. **Code.** `binBodyGenerator.py`: `raisedCornersBottomZ` from the start depth as a Dim expression
   (`binBodyTotalHeight − max(tabTopOffset, support wall height + lipInnerInset − wall)`), used only for the corner
   sections, chain and fallback fillet; the raised divider boxes keep their bottom. `entry.py` ledge check passes the
   bin's lip type and wall. Code comments: root cause, rejected alternatives (moving the section to the support's tip:
   leaves the support sharp against the divider and a step to the corner fillet below).
3. **Shape cases.** Two new cases (spec), JSON + `settings.json`; README of the e2e cases.
4. **Fusion (slot via main session).** Diagnosis script on A and B with the fix: pictures of the junctions, chain
   log, ledge notes; then snapshot runs of the new cases, `…_3_columns_lip_full` (update after looking), the two
   light-lip raised divider cases. Sketches fully constrained (checked by the snapshot run).
5. **CHANGELOG** `## Unreleased` → `### Raised dividers under a full lip`; click test checklist
   `dev-notes/klicktest-r50.md`.
6. **Review** by an Opus subagent, findings fixed. Then PR text to the main session, push, PR, CI.
