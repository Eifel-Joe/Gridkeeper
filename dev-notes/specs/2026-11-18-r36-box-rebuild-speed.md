# Round 36: box rebuild keeps joints on the right part; faster preview, build and rebuild

Points: p293 (error), p295, p296 (improvements). Box after Pred's parametric Gridfinity Storage Box v1.1
(https://www.printables.com/model/543553, CC BY-NC, by Pred).

## p293 "Box-Rebuild: eigenes Gelenk an einem Riegel springt auf den letzten Riegel"

### Problem
A user joint on one of the four latches (or a handle pin or hinge) lands on the last latch after a box rebuild.
`rebuildUtils.repointJointsByName` keys the new set's joint origins by `(partRole(component), jointOrigin.name)`.
The four latches are four occurrences of one component (`predBoxInsert.insertParts`, `addExistingComponent`), so the
four `("Latch", "Latch joint origin")` entries overwrite each other and the last occurrence wins. The old side is keyed
the same way, so which latch the joint was on is lost.

### Requirement
A user joint on a joint origin of a small part goes to the same part at the same seat in the rebuilt set: latch
front left stays on latch front left, handle pin right on handle pin right, hinge 2 on hinge 2. Joints on box and lid
(one occurrence each) behave as before.

### Options
1. Occurrence order: the n-th occurrence of a component in the old set maps to the n-th in the new one. Relies on
   Fusion's child order and on nothing being added in between; breaks silently.
2. Seat (chosen, the idea in the point): every part occurrence is jointed by the set's own joint to a box joint origin
   `"<seat> joint origin"` (`predBoxParts.seatJointOriginName`). The seat names the occurrence, independent of order
   and of the set's name.

### Decision
Key = (place, seat, joint origin name). Seat comes from the set's own joints: the joint whose one side is the part
occurrence and whose other side is a box joint origin whose name is a seat joint origin. Occurrences without a seat
(box, lid, a set of an older build) get seat `''`, as today. Fusion-free helpers (seat from a joint origin name,
seat per occurrence path from a list of joint ends) carry the logic and get unit tests.

### End-to-end criterion
In Fusion: box built, a user joint from a free body/component onto the joint origin of "Latch front left" (second
case: "Handle pin right"), box rebuilt (other size); afterwards the joint's box side is the occurrence jointed at
"Latch front left" (resp. "Handle pin right") of the new set, joint healthy.

## p295 "Box-Vorschau fügt die Kleinteile jedes Mal neu ein (langsam)"

### Decision
The preview (`mayChangeDocument=False`, new box and rebuild preview) builds box and lid only, without the small parts.
Decided after the Fusion measurement (p296): the preview makes no joint origins either (cells, stack, seats, lid) and
no lid joint; they took 20–100 s, 75 s in a preview, and nothing reads them there. OK builds as before, with parts
and every joint origin. The dialog's preview
text says that the preview shows box and lid without the small parts.

### End-to-end criterion
Preview time before/after measured; in the click test the preview shows box and lid without parts, OK gives the
complete set.

## p296 "Box-Bau und Rebuild mit Kleinteilen sind langsam"

### Approach
Measure first (fusion-auftraege/r36_mess.py: phase timers and cProfile for first box, second box, rebuild). Then
speed up where the time goes, only measures that keep the result identical (same bodies, joints, parameters, timeline
health). Candidates, to be confirmed or dropped by the measurement:
- part generators drawn once per set already; check whether compute after each operation (parametric, marker at the
  end) dominates, e.g. joints added with the full design recomputing;
- rebuild deleting the old group item by item (`removeOldGroup(oneByOne=True)` once a joint moved);
- a second box costing twice the first (something scaling with the document).
The decision per measure is recorded in the plan with the numbers.

### End-to-end criterion
Times before/after for build, second build and rebuild of the same 5x4x6 box, with result checks unchanged (bodies,
volumes, joints healthy, sketches fully constrained).

## Not part of this round
- Changing geometry of box, lid or parts.
- A different joint structure of the set (rigid joints at seats stay).
- Version number (stays 1.1.0); CHANGELOG under `## Unreleased`.
