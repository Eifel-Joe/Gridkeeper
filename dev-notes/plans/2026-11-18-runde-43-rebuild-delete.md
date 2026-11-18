# Plan round 43: rebuild deletion, joint names

Spec: `dev-notes/specs/2026-11-18-runde-43-rebuild-delete.md`. TDD per task, full `python -m pytest` after each, one
commit per green task (English messages).

- [x] **T1 `jointNames.freedName`** — new `lib/gridfinityUtils/jointNames.py` (no Fusion import).
  Test `tests/test_joint_names.py`: "X in cell (1)" with nothing taken → "X in cell"; base taken → None for "(1)";
  "X (3)" with base and "(1)" taken → "X (2)"; no counter → None; "Probe (x)" → None.
  RED: module missing. GREEN: regex `^(.*) \((\d+)\)$`, candidates base, base (1) … base (n-1).
- [x] **T2 `timelineRemoval.deleteMovedFirst(items, isMoved, timeline, log)`** — returns names kept (suppressed).
  Tests in `tests/test_timeline_removal.py` with the existing stand-ins, timeline gets `timelineGroups.add(start, end)`
  and items an `index`:
  moved items deleted one by one first, then one new group over the rest deleted whole, marker at the end;
  a moved item Fusion won't delete → rest item by item; rest not contiguous → item by item; whole delete returns False
  or raises or leaves items → its header off, the rest item by item; nothing moved → straight to the whole delete.
  RED: function missing. GREEN: implement.
- [x] **T3 `rebuildUtils`: note moved joint origins, use them** — `RebuildTarget.movedFrom: list`; `repointJoints` and
  `repointJointsByName` append the native old joint origin of each joint moved; `removeOldGroup(target, oneByOne)` with
  joints moved: group header off, `timelineRemoval.deleteMovedFirst(target.groupItems, isMoved, …)` where isMoved
  compares `JointOrigin.cast(item.entity)` with `target.movedFrom`. Tests on stand-ins / source as
  `tests/test_rebuild_joint_ends.py` does: both repoint functions append on a move and not on a note; removeOldGroup
  calls deleteMovedFirst when joints were moved and no longer `deleteOneByOne` over all items.
- [x] **T4 `rebuild`: names without counter** — tokens of `rootComponent.allJoints` before the build; after
  `removeOldGroup` each new joint with `freedName(...)` not None is renamed (names of the other joints of its
  component as taken). Not on a preview. Test on stand-ins of design/joints: new "B in cell (1)" → "B in cell", an old
  joint isn't touched, a taken base keeps the counter.
- [x] **T5 Fusion e2e** `fusion-auftraege/r43_e2e.py` (frozen, dry-checked, slot from the main session): steps plate,
  pocket, names (each < 50 s); box (build 5×4×6 + probes, long) and boxrebuild (long, via runner) measuring
  `removeOldGroup`. Snapshot cases: none affected (no geometry change).
- [ ] **T6** CHANGELOG `## Unreleased` → `### Rebuild deletion (round 43)` with measured values only;
  `dev-notes/klicktest-r43.md`; Opus review; PR text to the main session; push, PR against master, CI.
