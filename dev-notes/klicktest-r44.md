# Click test round 44 (p570)

Add-in loaded from the round 44 worktree; before clicking, Stop/Run the add-in once in "Scripts and Add-Ins" (a script
switch leaves the menu commands dead). New document, nothing saved. Names are read in the browser tree.

| # | Steps | Expected |
|---|---|---|
| 1 | New component by hand, rename it to "Gridfinity bin 1x1x3 (5)". Bin 1×1×3 with "Snap to free spot" (no cell). | Bin component "Gridfinity bin 1x1x3", the hand-made "(5)" unchanged. |
| 2 | Right click the bin › rebuild, change it to Solid, OK. Rebuild again as Hollow. | After each rebuild the bin is "Gridfinity bin 1x1x3" again, no "(1)" / "(2)"; "(5)" unchanged. |
| 3 | Baseplate 2×2 with joint origins, bin 1×1×3 into socket 2-2. Rebuild the bin (Solid). | Bin component without counter, still in cell 2-2. |
| 4 | Rebuild the baseplate of step 3 (Full → Light). | Baseplate component named as before the rebuild, no "(1)"; bin stays in cell 2-2. |
| 5 | Cullenect bin 1×1×3, insert into its pocket. Rebuild the insert twice (Debossed, then Embossed). | Insert component and its "Text" component named as after building, no counter. |
| 6 | Second bin 1×1×3 next to the first (Fusion names it "Gridfinity bin 1x1x3 (1)"). Rebuild that second bin. | It stays "Gridfinity bin 1x1x3 (1)": the first bin still holds the name without counter. |
| 7 | Box 5×4×6, rebuild as 6×4×6. | Set, box, lid and small parts without "(n)" from the rebuild; timeline healthy. |
| 8 | Insert whose first line is "M3", rebuild it with the first line "M3 (2)". | Insert component ends in "M3 (2)", the "(2)" is kept. |
