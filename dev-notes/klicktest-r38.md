# Click test round 38: GridfinityGenerator 2.5 merged

Add-in loaded from `wt-r38` (branch `r38-upstream-2-5`). A new design for each part unless a step says otherwise.

## Bin dialog

| # | Steps | Expected |
|---|---|---|
| 1 | New design without baseplate or box, open **Gridkeeper bin** | Group **Placement** right under Info, expanded, with only **Position** = *Snap to free spot*; no **Cell**. **Main dimensions** has no placement input any more |
| 2 | Position *Center on origin*, OK | Bin 2 × 3 centered on the origin (its footprint from −x to +x, −y to +y) |
| 3 | Build a second bin with *Snap to free spot* | It goes beside the first one, not on top of it |
| 4 | **Gridkeeper rebuild** the centered bin, Bin width 3, OK | Still centered on the origin with its new width |
| 5 | Rebuild the centered bin again, change only **Base width unit** to 40 mm | Rebuilt (not only parameters set) and still centered |
| 6 | Design with a baseplate built with **Add joint origins**, open **Gridkeeper bin** | **Placement** has **Cell** and **Position** |
| 7 | Set Position *Center on origin*, then pick a socket joint origin as Cell | **Position** turns grey as soon as the cell is picked; clearing the cell makes it active again |
| 8 | With the cell picked, OK | Bin jointed into the cell (joint *… in cell*), not at the origin. Its settings (Gridkeeper settings) show no Position line or *Snap to free spot*, never *Center on origin* |
| 9 | **Bin compartments › Label tab**: Add label tab, **Tab top offset (mm)** | Input present, 0.5 mm by default; typing 2.5 mm is refused (red), 0 and 2 mm are taken |
| 10 | 3 compartments, Add label tab, Tab top offset 2 mm, OK | Tabs and dividers 2 mm below the top |
| 11 | As 10 with **Dividers up to the top** and Label style *Cullenect* | Raised dividers meet the lowered dividers without a gap or step; each tab has its Cullenect pocket; a Cullenect insert (**Gridkeeper label**, pick the pocket) sits flush in it |
| 12 | Add magnet sockets on, OK, look at the bottom | Each magnet socket has a small chamfer around its opening |
| 13 | **Load from file** a bin settings file saved before this version (no `placement`, no `tabTopOffset`) | Loads without notes about these two; Position *Snap to free spot*, Tab top offset 0.5 mm |

## Baseplate dialog

| # | Steps | Expected |
|---|---|---|
| 14 | **Gridkeeper baseplate**, Baseplate type *Light* or *Full* | **Add connection holes** and **Connection hole diameter** greyed out |
| 15 | Type *Skeletonized* | **Add connection holes** active; **Connection hole diameter** active only when the box is ticked |
| 16 | Skeletonized 2 × 2, connection holes on, **Add side padding** left 5 mm, bottom 3 mm, OK | Connection holes only on the right and back sides, none on the padded left and front |
| 17 | Full plate with magnet cutouts, OK | Magnet sockets with a chamfer around their opening |
