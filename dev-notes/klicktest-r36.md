# Click test round 36 (box dialog: preview, rebuild with a joint on a small part)

Add-in loaded from the worktree `wt-r36`, Fusion restarted, a new design.

| # | Step | Expected |
|---|---|---|
| 1 | Gridkeeper box, 5 × 4 × 6, tick **Show preview (slow)**, hover the checkbox | Tooltip: the preview shows box and lid, the small parts come with OK |
| 2 | With the preview on, look at the model and the browser | Box and lid shown, no latches, handle, pins or hinges; *Last preview* shows a time (note it) |
| 3 | Change Width to 6 with the preview on | Preview follows, again without small parts, time noted |
| 4 | Width back to 5, OK | Set *Box 5×4×6* with Box, Lid, 4 × Latch, Handle, 2 × Handle pin, 2 × Hinge; nothing unhealthy in the timeline |
| 5 | New component *Probe* with a joint origin; joint it rigidly onto *Latch joint origin* of the front left latch (the one at joint *Box 5×4×6 Latch front left*) | Probe sits at the front left latch |
| 6 | Right-click the box, **Gridkeeper rebuild**, preview on | Preview shows box and lid without small parts, the old set hidden |
| 7 | Width 6, OK | Set *Box 6×4×6* with all parts; Probe still at the **front left** latch (not at the right latch at the back); joint healthy |
