# Runde 34: label tab of a shelled bin with a lip and a scoop under the full lip (p281)

## Problem
The shelled bin builder (`commands/commandCreateBin/binBuilder.py`, tab block after the shell) places the label tab at
`BIN_LIP_WALL_THICKNESS` from the front when `binBodyInput.hasLip and binBodyInput.hasScoop`. That value is the inner
edge of the light lip; a full lip's inner tip lies elsewhere (`lipInnerInset`). Inherited from the original generator
(Le0Michine, FusionGridfinityGenerator). Decided: fixed in this fork only, nothing goes towards the original.

## Finding (code evidence, before any change)
- `binBuilder.py:361`: `binBodyInput.hasScoop = state.hasScoop and isHollow and not shaped`. A shelled bin is
  `BIN_TYPE_SHELLED`, so `isHollow` is false and `binBodyInput.hasScoop` is always false there. The scoop is not built
  for shelled bins (`binBuilder.py:141` says the same for creases). Nothing else assigns the field.
- So the branch `if binBodyInput.hasLip and binBodyInput.hasScoop` in the shelled tab block (`binBuilder.py:566`) can
  never run. A shelled bin with lip, scoop and full lip puts its tab on the back wall like any shelled bin, whatever
  the lip type. The reported misplacement cannot occur.
- The hollow bin with scoop already follows the lip type: `compartmentsMinY = lipInnerInset(lipType, xyClearance)`
  (`binBodyGenerator.py:171`), snapshot `bin_2x2x4_lip_full_scoop_tab`; its tab sits on the back wall.

## Options
1. Remove the dead branch, so the code says what happens (tab on the back wall). Test pins the behaviour.
2. Make the dead branch follow `lipInnerInset`. Rejected: it keeps code that cannot run and suggests a scoop on shelled bins.
3. Leave as is. Rejected: misleading code that stays a trap if the scoop is ever allowed on shelled bins.

## Decision
Option 1. The dialog's scoop checkbox stays enabled for shelled bins and has no effect there, as before; not part of
this round.

## Not part of this round
Scoop on shelled bins, greying the scoop checkbox for shelled bins, anything of the full lip support.

## End-to-end criterion
One new snapshot case `bin_2x1x3_shelled_lip_full_scoop_tab` (shelled, lip Full, scoop on, tab on): built in Fusion,
the tab sits on the back wall, no scoop in the body, all sketches fully constrained. Unit test: the tab origin of a
shelled bin is independent of `hasScoop` and the lip type.

## Plan
1. Fusion job (slot): build the new case with the current code, check tab position and that no scoop exists. (Evidence.)
2. RED: pytest that pins the shelled tab origin (extract the placement into a small pure function
   `shelledTabOriginY(binLength, baseLength, xyClearance)` in `binBuilder.py`); GREEN: use it, delete the branch.
3. New snapshot case file, CHANGELOG entry under `## Unreleased`, Opus review, PR.
