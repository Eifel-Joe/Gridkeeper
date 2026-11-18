# Plan round 36 (p293, p295; p296 after measuring)

Spec: dev-notes/specs/2026-11-18-r36-box-rebuild-speed.md. Tests: `python -m pytest`.

## Task 1: seat from a joint origin name (p293)
- [ ] Test `tests/test_pred_box_parts.py`: `seatOfJointOriginName('Latch front left joint origin') == 'Latch front left'`,
  every seat of `SEAT_NAMES` round-trips, `'Lid joint origin'`, `'Label joint origin'`, `'Latch joint origin'` give `None`.
  RED: no such function.
- [ ] `predBoxParts.seatOfJointOriginName`. GREEN.

## Task 2: seat per part occurrence from the set's joints (p293)
- [ ] Test `tests/test_box_rebuild_seats.py` (stand-ins, function loaded from rebuildUtils source like
  test_bin_cell_rebuild): `seatsByOccurrence(joints)` maps the occurrence on the other side of a seat joint origin to the
  seat, either side order, falls back to the other joint origin's assemblyContext when the joint has no occurrence,
  ignores joints without a seat joint origin. RED: missing.
- [ ] `rebuildUtils.seatsByOccurrence`. GREEN.

## Task 3: keys with the seat (p293)
- [ ] Tests in the same file: `newJointOriginKeys(newPart, seats)` gives four distinct latch keys
  `('Latch', '<seat>', 'Latch joint origin')` for four occurrences of one component, box/lid keep seat `''`;
  `oldJointOriginKey(jointOrigin, oldComponents..., seats)` gives the same key for the old latch at the same seat; the
  joint on old "Latch front left" picks the new occurrence at "Latch front left", not the last one.
  RED: missing.
- [ ] Extract the key building of `repointJointsByName` into these two functions, keyed (place, seat, name). GREEN.
- [ ] Source test: `repointJointsByName` uses `seatsByOccurrence`, `newJointOriginKeys`, `oldJointOriginKey`.

## Task 4: preview without small parts (p295)
- [ ] Test `tests/test_box_builder_bodies.py`: `_buildBox` takes `withParts`, `insertParts` only under
  `withParts`; `buildBox` passes `mayChangeDocument` as `withParts`; the seat joint origins stay unconditional
  (besides the component guard). RED.
- [ ] Implement; the preview checkbox tooltip says the preview shows box and lid without the small parts. GREEN.

## Task 5: CHANGELOG, click-test checklist
- [ ] `CHANGELOG-CULLENECT.md` under `## Unreleased`, group `### Box rebuild and preview (round 36)`.
- [ ] `dev-notes/klicktest-r36.md`.

## Task 6: Fusion evidence (slot from the main session)
- [ ] p293 end-to-end script: build box, user joint onto "Latch front left" and "Handle pin right", rebuild 6x4x6,
  joints on the occurrences at those seats, healthy.
- [ ] Measurement r36_mess.py before (master code) and after; p296 plan section with the numbers.
