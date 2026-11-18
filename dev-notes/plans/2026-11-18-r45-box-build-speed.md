# Plan round 45 (p296, p480)

Spec: dev-notes/specs/2026-11-18-r45-box-build-speed.md. Tests: `python -m pytest`.

## Task 1: Dim knows whether it depends on parameters (B)
- [ ] Tests in `tests/test_dim_linear.py`:
  - `Dim.length`, `Dim.number`: `dependsOnParameters` false; `Dim.parameter` (stand-in with name and value): true.
  - `(W * 42 mm + 20 mm - 21 mm) - (W * 42 mm + 20 mm - 41 mm)` false; `W * 42 mm - 21 mm` true; `W - W` false;
    `W / 2 - W * 0.5` false; `W * 2 - H * 2` true.
  - `.abs()` of a difference that cancels: false; `.abs()` of `W - 1 mm` true; `abs(A) - abs(A)` (same text) false.
  - `Dim.min(A, B) / 2 - Dim.min(A, B) / 2` false; `Dim.min(A, B) - Dim.min(A, C)` true.
  - A product or quotient of two parameter dims is one part: `W * H - W * H` false, `W * H - H * W` true (only the same
    text cancels; on the safe side).
  - kind and expression text exactly as today for every case above (existing `tests/test_dim.py` stays green).
  RED: no `dependsOnParameters`.
- [ ] `dim.py`: an optional linear form (`dict` part → coefficient, `None` key for the constant) carried through
  `_combine`, `_function`, `abs`, `asExpression`, `Dim.parameter`; `dependsOnParameters`. GREEN, full suite.

## Task 2: WorldSketch leaves constant dimensions alone (B)
- [ ] Tests in `tests/test_pred_sketch_constant.py` (Fusion-free with stand-ins for sketch, dimensions and parameter,
  as far as `_apply` runs on them; else AST like `test_pred_sketch_fixed`): an `hdim`/`vdim` whose world difference
  cancels gets no expression set, one that hangs on a parameter does (as today); a constant diameter likewise.
  RED.
- [ ] `predSketch._apply`: `applyTo` only when `value.dependsOnParameters`. GREEN, full suite.

## Task 3: box joint origins without sketches (A)
- [ ] Tests in `tests/test_offset_joint_origins.py`: `createOffsetJointOrigins` with stand-ins (component with
  `originConstructionPoint`, `jointOrigins.createInput/add`): one joint origin per point, on the origin point, offsets
  `valueInput` of x, y, z (expression for a parameter dim, number otherwise, negative stays negative), names as given,
  returned in order; no sketch, no plane made. Source checks: `boxBuilder._buildBox` and
  `predHandlePin.createHandlePin` call `createOffsetJointOrigins` and no longer `createPointJointOrigins`; the `forOk`
  guard (test_box_builder_bodies) holds for the new name; bin, baseplate and label builders unchanged. RED.
- [ ] `baseGenerator.createOffsetJointOrigins`; the call sites; existing source tests that name
  `createPointJointOrigins` for the box move to the new name. GREEN, full suite.

## Task 4: edges and faces looked up by point (C)
- [ ] Tests in `tests/test_pred_box_pick.py` (Fusion-free part in `predBoxEdges`):
  - `probePoint(item)`: line → midpoint of its ends; arc → its start; face → middle of its box.
  - `pickByPoint(expected, find, key)`: `find(item)` gives the candidates near the item; matched by `_signature` as in
    `matchItems`; returns the picked list or `None` when any item isn't found (caller falls back).
  - Same edges as `matchItems` over all candidates for a stand-in body (lines, arcs, faces; a candidate of another
    body is not taken).
  RED.
- [ ] `predBoxEdges.probePoint/pickByPoint`; `_Builder._pick` uses them with `component.findBRepUsingPoint`
  (edges / faces, tolerance 1e-5, filtered to the body), falls back to today's walk with a `debugLog` line;
  `floorGrid` blend edges by a point midway up each expected edge, fallback today's walk. GREEN, full suite.

## Task 5: CHANGELOG, click-test checklist
- [ ] `CHANGELOG-CULLENECT.md` `## Unreleased`, group `### Box build speed (round 45)`, measured numbers only.
- [ ] `dev-notes/klicktest-r45.md`: box from the dialog (OK) with parts, bin from the bin dialog into a box cell,
  stacking two boxes by their joint origins, parameter change, rebuild with a user joint on a latch.

## Task 6: Fusion evidence (slots from the main session)
- [ ] `r45_mess.py` = `r39_mess.py` with REPOS branch wt-r45 / base `_scratch/r45/base` (detached worktree of 794253f),
  plus a count of joint-origin sketches, expressions set and C fallbacks per build. Base and branch back to back.
- [ ] Box snapshot cases box_5x4x6, box_5x4x6_params_7x5x10, box_6x5x7_params_4x3x6, box_5x4x6_lid_closed_params_4x3x8.
- [ ] Numbers into this plan and the PR.

## Measured (Task 6, 18.11.2026)
`fusion-auftraege/r45_mess.py` (branch, then base 794253f, same Fusion session, new hybrid document each run) and
`r45_nach.py` (branch box 1/2 again on the final head after the review fixes):

| Step | Base 794253f | Branch | Branch final |
|---|---|---|---|
| Box 1 5×4×6 with parts | 115.4 s, 965 parameters | 81.0 s, 877 | 75.2 s, 877 |
| Box 2 beside it | 214.1 s, 1946 in all | 143.1 s, 1770 | 146.8 s, 1770 |
| Rebuild box 1 as 6×4×6, two probe joints (p293) | 471.1 s, green | 315.9 s, green | – |
| Preview | 196.5 s | 122.7 s | – |
| Width of box 2 5 → 6 | 12.1 s, +42 mm, healthy | 12.8 s, +42 mm, healthy | – |
| Rebuild preview (p481) | 231.8 s, green | 143.4 s, green | – |

Branch: no joint-origin sketches, every sketch of the sets fully constrained, no fallback of the edge lookup on the
final head (the first branch run had three face lookups fall back: #56, #77, #82, rounded corner and L-shaped faces whose
box middle lies off them; fixed with a grid of probe points). Latch area and volume identical to base.
