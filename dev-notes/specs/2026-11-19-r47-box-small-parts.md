# Round 47: the box's small parts faster, stale latch snapshots

Points: p591 (small parts of the box faster), p592 (stale latch area in six box snapshots). Box and small parts after
Pred's parametric Gridfinity Storage Box v1.1 (https://www.printables.com/model/543553, CC BY-NC, by Pred), drawn in
code (rounds 27–29, 40).

## What was measured (Fusion, master fa10e31, 19.11.2026)

Script `fusion-auftraege/r47_mess.py`, log `r47_mess.log`. Box 5×4×6 with the default hinge (M3x30), one new hybrid
document; `drawPart` timed per role.

| | Latch | Hinge | Handle | Handle pin | Rest of `insertParts` (components, joints, colour) | All parts |
|---|---|---|---|---|---|---|
| Box 1 (build 70 s) | 12.7 s | 11.4 s | 3.1 s | 2.6 s | 3.2 s | 32.9 s |
| Box 2 beside it (build 139 s) | 19.1 s | 20.2 s | 6.4 s | 6.1 s | 6.4 s | 58.2 s |
| The four parts once more into the root of that document (no set, no joints) | 17.4 s | 17.3 s | 7.0 s | 4.7 s | – | 46.4 s |
| The four parts in a new, empty hybrid document | 3.5 s | 4.3 s | 0.8 s | 0.7 s | – | 9.3 s |
| The four parts in a new document without history (direct) | 2.7 s | 1.3 s | fails | 0.3 s | – | – |
| The bodies of box 2's parts copied (`TemporaryBRepManager.copy`) into a new component each, as a base feature, in the full document | 1.0 s | 1.2 s | 1.0 s | 1.0 s | – | 4.2 s |

- The parts' own work is small; what costs is the document they are drawn in: each feature in a document with boxes
  pays for the boxes' model parameters (as round 39/45 found for the box itself).
- A copied body has the same area and volume as the original (all four, to 1e-9).
- Direct (no history) is no way: the handle needs a parameter its sketch dimension has none of there, and the latch's
  area comes out 3085.729306 instead of 3085.723822 mm².

## Decided before the spec

- Latches, hinges and handle pins need no parameters and no history, finished bodies are fine; the handle keeps one
  parameter, its width. Condition: it must work — joints and seats, the rebuild moving user joints over (p293), export,
  colour and the snapshots stay intact.

## Probe: where the parts can be drawn inside the box command

`fusion-auftraege/r47_cmdprobe.py` (log `r47_cmdprobe.log`), a command with a dialog like the box command's (an input,
a browser input, executePreview, inputChanged and validateInputs handlers; pattern of round 28's `r28_cmdvariants` V4),
the latch drawn in its execute:
- A hidden helper document: `Documents.add(..., visible=False)` raises "API Function not yet implemented". A visible
  one works (3.5 s, the command's document active again after closing it), but the user would see a document open and
  close: not taken.
- The latch drawn into a scratch component of the command's document, its body kept as a temporary body, the scratch
  occurrence deleted (0.1 s), the body added to the target component as a base feature (0.1 s): same area, timeline
  healthy, nothing left of the scratch component. Taken.

## Requirement

1. Latch, hinge (per variant) and handle pin are kept per Fusion session as temporary bodies
   (`TemporaryBRepManager.copy`) with their names, in memory of the add-in. The first box that needs one draws it, by
   the generators there are (predLatch, predHinge, predHandlePin, geometry unchanged), into a scratch component of its
   set, copies the bodies and deletes the scratch occurrence again.
2. Every box set gets those parts as copies: per part a component as before (same name, role tag, occurrences,
   colour), holding one base feature with the copied bodies, named as drawn (Latch, Handle pin, the hinge's bodies by
   Pred's names). Each gets its joint origin as before, made by the same code as today (latch: on the origin, Z along
   +y, X along x, 180°; pin: its offset joint origin; hinge: on the origin), same names, so joints, seats and the
   rebuild's moving of user joints by name (p293) work unchanged.
3. The handle is drawn in the set as today, with its width expression on the box parameters (its one parameter).
4. If drawing into the scratch component, the copy or the base feature fails, the part is drawn in its component as
   today and the reason logged (`commonUtils.fileLog`); the box is built either way.
5. Geometry unchanged: the box snapshot cases pass with the stored part values (after p592).
6. p592: the six stale cases (box_4x3x8, box_5x3x9, box_5x4x6_params_7x5x10, box_6x5x7, box_6x5x7_params_4x3x6,
   box_7x5x10) get the latch's values the code draws (area 3085.723822 mm², volume unchanged), recorded once after
   p591, nothing else of them changed. Shown by the snapshot run: before review on the latch's area only, after pass.

## Expected (measured after the change, same steps as `r47_mess.py`)

- The first box of a Fusion session: about as today (the three parts drawn once, in the full document), plus about
  0.1 s per part for copy and base feature.
- Every further box and every rebuild in that session: the three parts about 0.1–1 s each instead of 8–20 s; box 2's
  parts about 15 s instead of 58 s (handle and joints stay).

## What changes for the user (decision, see above)

- In a box set the components Latch, Handle pin and Hinge hold one base feature each instead of their sketches,
  planes, extrudes, fillets and chamfers; the set's timeline is shorter, the parts cannot be edited through their
  history. The handle is unchanged.
- The document gets fewer model parameters per box, so every later box in the document gains as well.
- Unchanged: places, joints and their names, the rebuild (parts made anew, user joints moved over), export by body
  names, colour, the preview (no parts), a change of the box parameters (the handle follows the width as before).

## Open for a decision of the user

- **Keep the parts on disk as well?** Written by the add-in itself as .smt (`TemporaryBRepManager.exportToFile`) into
  its settings folder after they were first drawn, keyed by the add-in version and the hinge variant, read back by
  `TemporaryBRepManager.createFromFile` (probe: 0.07 s there and back). Then the first box of a session is fast too.
  It touches the project rule "parts never by import, drawn in code" (the parts are still drawn in code, but read
  from a file the add-in wrote); not built unless decided. Recommendation: not now, the session cache covers every
  box after the first.

## Not part of this

The handle's other sketch dimensions (constant already since round 45, `Dim.dependsOnParameters`), bins, baseplates,
labels.
