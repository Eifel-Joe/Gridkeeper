# Click test round 39: box build, preview and rebuild

Add-in loaded from the round's worktree, a new document, Fusion's text command window open for the log.

| # | Step | Expected |
|---|---|---|
| 1 | Box dialog, defaults (5×4×6), preview off, OK | Set "Box 5×4×6" with box, lid, latches, handle, pins, hinges; timeline healthy; every sketch of the set fully constrained (sketch icons without the open-constraint mark) |
| 2 | Open one latch sketch and one box wall sketch | Points that hang on no box size are fixed (lock icon), points on the size and the ends and centres of arcs keep their dimensions |
| 3 | Change parameter `gfBox1_baseWidth` 5 → 6 in Change Parameters | Box and lid 42 mm wider, small parts on their seats, timeline healthy |
| 4 | Box dialog again, preview on, change width once | Preview shows a second box and lid; nothing left in the timeline after Cancel |
| 5 | Select the first box's body, box dialog (rebuild), preview on, length 4 → 5 | Preview shows the new box and lid; the old set is not visible; the log has no "Cannot suppress" line |
| 6 | Cancel the dialog of step 5 | The old set is visible again, nothing else changed |
| 7 | Step 5 again, then OK | Set rebuilt in place, old set gone, a joint of the user on a latch (made before) stays on the latch at the same seat, timeline healthy |
| 8 | Rebuild preview of step 5, then change an input so the preview recomputes, then Cancel | Old set visible after Cancel |
| 9 | Two boxes in the document, a joint of the user on a latch of the first, rebuild the first (other size), OK | Rebuild finishes, no error; the joint stays on the latch at the same seat; the second box untouched |
