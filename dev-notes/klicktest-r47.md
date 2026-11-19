# Click test round 47: the box's small parts as session copies

Add-in loaded from the round's worktree after a restart of the add-in (so the session cache is empty), a new
document, Fusion's text command window open for the log.

| # | Step | Expected |
|---|---|---|
| 1 | Box dialog, defaults (5×4×6, hinge M3x30), preview on, then OK; note the time ("generated in …") | Preview shows box and lid only; after OK the set "Box 5×4×6" with box, lid, 4 latches, handle, 2 pins, 2 hinges, all parts in the box parts colour; timeline healthy; no line "drawn in place" in the log |
| 2 | Browser: open the components Latch, Handle pin, Hinge of the set | Each holds one base feature and its joint origin ("Latch joint origin", "Handle pin joint origin", "Hinge joint origin"), no sketches; the Handle component still has its sketches and features; no leftover component "Component …" in the set |
| 3 | Look at the parts on the box | Latches at the front and at the back sides, handle with its pins at the front, hinges beside the box in print position, as with master |
| 4 | Box dialog a second time, defaults, OK; note the time | Second set beside the first, clearly faster than the first box (parts copied); same checks as 1 and 2 |
| 5 | Box dialog, hinge "Pinned", OK | Third set with the pinned hinge (its printed pin as body "Hinge pin"), no line "drawn in place" |
| 6 | User joint (rigid) from a new component to a latch of the first box; select the first box, box dialog (rebuild), width 5 → 6, OK | Set rebuilt in place, the user joint on the latch at the same seat, handle 14.5 mm wider, parts again one base feature each, timeline healthy |
| 7 | Change parameter `gfBox2_baseWidth` 5 → 6 | Second box and lid 42 mm wider, its handle wider (it follows the width), latches, pins and hinges on their seats, timeline healthy |
| 8 | Export (Gridkeeper export) of the second set as separate parts | Files for Latch, Handle, Handle pin, BottomHingePart_M3x30, TopHingePart_M3x30 besides box and lid, each part shaped as before |
