# Click test round 43 (p533, p430)

Add-in loaded from the round 43 worktree; before clicking, Stop/Run the add-in once in "Scripts and Add-Ins" (a script
switch leaves the menu commands dead). New document, nothing saved.

| # | Steps | Expected |
|---|---|---|
| 1 | Baseplate 2×2 with joint origins. Bin 1×1×3 into socket 2-2 (Bin dialog, cell picked). | Bin in cell 2-2, joint "… in cell". |
| 2 | Right click the bin › rebuild, change it to Solid, OK. | Bin still in cell 2-2; the joint is named "… in cell" again, no "(1)". |
| 3 | Right click the baseplate › rebuild, Full → Light, OK. | Rebuild done within seconds; the bin stays in cell 2-2 of the new baseplate; timeline without warnings; the old baseplate is gone. |
| 4 | Cullenect bin 1×1×3, insert into its pocket (Label dialog). Rebuild the insert (surface Debossed). | Insert in the pocket, its joint "… in pocket" without "(1)". |
| 5 | Rebuild the bin of step 4 as 1×2. | Insert stays in the pocket of the new bin, timeline healthy, old bin gone. |
| 6 | Box 5×4×6 with a bin jointed into floor cell 1-1, rebuild the box as 6×4×6. | Bin in cell 1-1 of the new box; the rebuild clearly faster than before (old set deleted in one go, see the add-in log: no "item by item"). |
| 7 | Rename a joint by hand to "Mine (2)", rebuild a bin next to it. | "Mine (1)" keeps its name. |
