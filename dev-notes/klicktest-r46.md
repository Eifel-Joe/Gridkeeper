# Click test round 46: joint origins of bins, baseplates and inserts without a sketch each

Add-in loaded from the round's worktree, a new document, Fusion's text command window open for the log.

| # | Step | Expected |
|---|---|---|
| 1 | Baseplate dialog, 6×6, joint origins on, OK | Baseplate 6×6; Browser › its component › Joint Origins: Socket joint origin 1-1 … 6-6 (36); no sketches "Socket joint origin sketch …" and no planes "Socket joint origin plane …"; timeline healthy |
| 2 | Show the joint origins (light bulb on the Joint Origins folder) | One in the middle of each socket at its bottom, as with master |
| 3 | Bin dialog, 2×1×3, label style Cullenect, place it into the baseplate's socket 2-2 (cell selection), OK | The bin stands in sockets 2-2/3-2, its joint "… in cell" healthy; the bin component has Foot joint origins, Pocket joint origin and Cell placement joint origin, no joint origin sketches or planes |
| 4 | Label dialog, insert 2u, pick the bin's pocket, OK | The insert lies in the pocket, its joint "… in pocket" healthy; its component has the Insert joint origin, no joint origin sketch |
| 5 | Bin dialog again, 1×1×3, without a cell (snap to free spot) | The bin goes to a free spot beside the others |
| 6 | Rebuild the baseplate (select it, baseplate dialog), type Light, OK | Rebuilt in place, the bin still in socket 2-2, timeline healthy |
| 7 | Rebuild the bin of step 3, height 3 → 4, OK | Rebuilt in place, still in socket 2-2, the insert on the floor of the new pocket |
| 8 | Rebuild the insert (select it, label dialog), other text, OK | Rebuilt, still in the pocket |
| 9 | Change the baseplate's parameter `gfBaseplate1_baseWidth` 42 → 50 mm | Baseplate wider; the bin follows socket 2-2; insert stays in the pocket; timeline healthy |
| 10 | Box dialog, defaults, OK; a bin into the box's cell 2-2; a box label | As before round 46 (the box isn't changed by this round) |
| 11 | Open or build a document with master (bin in a baseplate socket, insert in its pocket), then load the round's worktree and rebuild baseplate, bin and insert | The old joint origin sketches disappear with the rebuilt items; joints still healthy, bin in its socket, insert in its pocket |
