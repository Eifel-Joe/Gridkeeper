# Click test round 45: box build speed

Add-in loaded from the round's worktree, a new document, Fusion's text command window open for the log.

| # | Step | Expected |
|---|---|---|
| 1 | Box dialog, defaults (5×4×6), preview off, OK; note the time the log gives ("generated in …") | Set "Box 5×4×6" with box, lid, latches, handle, pins, hinges; timeline healthy; every sketch of the set fully constrained; no line "walking the whole body" in the log |
| 2 | Browser: Box component › Joint Origins | Cell joint origins 1-1 … 5-4, stack bottom, lid, the seats; no sketches named "… joint origin sketch …" and no planes "… joint origin plane …" in the Box and Lid components |
| 3 | Show the joint origins (light bulb on the Joint Origins folder) | Cell joint origins on the floor in the middle of each cell, stack bottom under the box middle, lid joint at the lid cut, seats at the latches, handle and pins, as in a box built with master |
| 4 | Bin dialog, 1×1×3, place it into the box's cell 2-2 (cell selection), OK | The bin stands in cell 2-2 of the box, its joint "… in cell" healthy |
| 5 | Change parameter `gfBox1_baseWidth` 5 → 6 | Box and lid 42 mm wider, small parts on their seats, the bin stays in cell 2-2, timeline healthy |
| 6 | Box dialog a second time, defaults, OK; note the time | Second set beside the first, no "walking the whole body" line; faster than a second box with master |
| 7 | Stack: joint the second box's "Stack bottom joint origin" to the first box's "Stack top joint origin" (Joint command) | The second box sits on the lid of the first |
| 8 | User joint (rigid) from a new component to a latch of the first box; then select the first box, box dialog (rebuild), length 4 → 5, OK | Set rebuilt in place, the user joint on the latch at the same seat, the bin still in its cell (joint moved by name), timeline healthy |
| 9 | Box label: add a label to the first box (box label dialog), then rebuild the first box again (width 6 → 5) | The label lies in front of the rebuilt box as before (not at the document origin) |
