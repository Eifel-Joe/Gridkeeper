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
- Only components the build named: every place that names a new component (assembly.addOccurrence and the
  containers, box and lid, the box's small parts) goes through `componentNames.name`, which records the requested
  name while a rebuild builds (`componentNames.recording`). Components the build didn't name, the user's own
  included, keep their names, also one named with an own "(n)".
- Only a name Fusion counted: the actual name is the requested one plus " (n)". A name the generator asked for with
  "(n)" at its end (e.g. from a label text "M3 (2)") stays, even though its base was the old part's name.
  Changed after the review: the first rule ("the base was taken before the build") counted the old part's own name
  as taken and would have dropped such a "(2)".
- A base another part still holds stays taken: the counter goes down only to the lowest free name, as with joints.
- Taken are the names of all components of the design after the old group is gone, the component itself excluded.
- A component Fusion won't rename keeps its name, logged, no error for the user; one gone again is skipped.

## Not in scope
- The user's own name of the rebuilt part itself: a rebuild names the new part after its settings as before.
- The box's `_renameParts` (round 27/28, role names) stays; the general step runs before it and takes the box set's
  own component too, which `_renameParts` didn't.
- Occurrence names follow the component name in Fusion, nothing to do.

## Plan
1. `lib/gridfinityUtils/jointNames.py`: no change, `freedName` is reused; a helper `countedBase(name)` (base of a
   counted name or None) added next to it, unit tested (`tests/test_joint_names.py`).
2. `lib/gridfinityUtils/componentNames.py` (`name`, `recording`), used at every place naming a new component;
   `lib/rebuildUtils.py`: `dropComponentCounters(design, named)`, `rebuild` records the names while `build` runs
   and calls the drop right after `dropJointCounters`. Tests first in `tests/test_component_names.py` and
   `tests/test_rebuild_delete.py` on stand-ins (named vs. not, user's own "(n)", base held by another part,
   generator's own "(n)" with the old part's base, rename raising, component gone) and the order in `rebuild`.
3. CHANGELOG-CULLENECT.md under `## Unreleased`, group `### Round 44: component names after a rebuild`.
4. Fusion check (one short e2e script, slot via main session): bin without cell, bin with cell, insert; each built,
   rebuilt twice, component name without counter; a component named by hand "Mine (2)" before stays.
5. `dev-notes/klicktest-r44.md`, review by an Opus subagent, PR.
