# Round 44: component names without Fusion's counter after a rebuild (p570)

## Problem
A rebuild builds the new part while the old one still exists, then deletes the old timeline group
(`rebuildUtils.rebuild`). Fusion keeps component names unique and counts a taken name up: a bin rebuilt without a
cell ("Snap to free spot") is named "Gridfinity bin 1x1x3 (1)", the next rebuild "(2)". Same cause as the joint names
of round 43 (p430, `dropJointCounters`), here for the component of the part.

## Goal
Once the old part is gone, every component the rebuild made whose name carries Fusion's counter gets the lowest free
name, by the same rule as joints (`jointNames.freedName`): the base first, then "base (1)" and on, never above its own.
Applies to every rebuild through `rebuildUtils.rebuild`: bin, insert (and its "Text" component), baseplate, box set,
box label. Not on a preview (it is undone anyway).

## Which names are touched
- Only components made by the build: those not among the components there were before (compared as objects, as the
  joints in round 43). Every component there was before, the user's own included, keeps its name, also one the user
  named with an own "(n)".
- Only a name Fusion counted: the base name without the counter was held by a component before the build. A name the
  generator itself gave with "(n)" at its end (e.g. from a label text) whose base wasn't taken stays as is.
- A base another part still holds stays taken: the counter goes down only to the lowest free name, as with joints.
- Taken are the names of all components of the design after the old group is gone, the component itself excluded.
- A component Fusion won't rename keeps its name, logged, no error for the user.

## Not in scope
- The user's own name of the rebuilt part itself: a rebuild names the new part after its settings as before.
- The box's `_renameParts` (round 27/28, role names) stays; the general step runs before it and takes the box set's
  own component too, which `_renameParts` didn't.
- Occurrence names follow the component name in Fusion, nothing to do.

## Plan
1. `lib/gridfinityUtils/jointNames.py`: no change, `freedName` is reused; a helper `countedBase(name)` (base of a
   counted name or None) added next to it, unit tested (`tests/test_joint_names.py`).
2. `lib/rebuildUtils.py`: `existingComponents(design)` (list of `design.allComponents`) and
   `dropComponentCounters(design, before)`; `rebuild` takes the components before `build` and calls the drop right
   after `dropJointCounters`. Tests first in `tests/test_rebuild_delete.py` on stand-ins (new vs. old, user's own
   "(n)", base held by another part, generator's own "(n)" with free base, rename raising) and the order in `rebuild`
   (after the preview return, before `build`, after `removeOldGroup`).
3. CHANGELOG-CULLENECT.md under `## Unreleased`, group `### Round 44: component names after a rebuild`.
4. Fusion check (one short e2e script, slot via main session): bin without cell, bin with cell, insert; each built,
   rebuilt twice, component name without counter; a component named by hand "Mine (2)" before stays.
5. `dev-notes/klicktest-r44.md`, review by an Opus subagent, PR.
