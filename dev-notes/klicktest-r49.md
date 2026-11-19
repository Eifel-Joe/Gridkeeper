# Click test round 49: the box's small parts kept on disk

Add-in loaded from the round's worktree. Its store is `partCache` in the worktree folder (`wt-r49\partCache`). Fusion's
text command window open for the log. A new document for each start of the add-in; nothing is saved. "Restart the add-in" means stop and run Gridkeeper by hand in Utilities › Add-Ins › Scripts and Add-Ins; a restart of Fusion is not needed.

| # | Step | Expected |
|---|---|---|
| 1 | Delete `wt-r49\partCache` if it exists. Restart the add-in, new document, box dialog with defaults (5×4×6, hinge M3x30), OK; note the time | Box set as with master (latches, handle, pins, hinges, colour, timeline healthy); `partCache` now holds six files `1.1.0-<12 hex>-Latch`, `…-Handle_pin`, `…-Hinge-M3x30`, each `.smt` and `.json`; no line "drawn in place" or "part file" in the log |
| 2 | Box dialog again, defaults, OK; note the time | Second set, clearly faster than step 1 (as in round 47); `partCache` unchanged |
| 3 | Restart the add-in, new document, box dialog with defaults, OK; note the time | Clearly faster than step 1 (the parts are read, not drawn); the set the same as in step 1: components Latch, Handle pin and Hinge with one base feature and their joint origins, parts on their seats, hinges in print position; no "part file" line in the log |
| 4 | Box dialog, hinge "Pinned", OK | Set with the pinned hinge (body "Hinge pin"); `partCache` gets `…-Hinge-Pinned.smt` and `.json` |
| 5 | Open `…-Latch.smt` in `partCache` in a text editor, replace its content with `x`, save. Restart the add-in, new document, box with defaults, OK | Box built as in step 1; the log has "part file 1.1.0-…-Latch.smt not read, drawn anew"; the Latch pair is written again (new time stamp); hinge and pin read |
| 6 | Put two files into `partCache`: `1.0.0-000000000000-Latch.smt` (any content) and `notes.txt`. Box dialog, hinge "Plain", OK | `…-Hinge-Plain` pair written; `1.0.0-000000000000-Latch.smt` is gone, `notes.txt` is still there; nothing outside `partCache` changed |
| 7 | Export (Gridkeeper export) of the box set from step 3 as separate parts | Files for Latch, Handle, Handle pin, BottomHingePart_M3x30, TopHingePart_M3x30 besides box and lid, shaped as before |
