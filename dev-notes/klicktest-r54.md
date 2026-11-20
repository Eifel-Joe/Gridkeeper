# Click test round 54 – centered bin follows its base units (p670)

Add-in loaded from `wt-r54` (branch `r54-centered-bin-follows-grid`), a new document, nothing saved.

| # | Step | Expected |
|---|---|---|
| 1 | Bin dialog: 2 x 1 x 3, Position *Center on origin*, joint origins on, OK | Bin centered on the origin: X −41.75 … +41.75 mm, Y −20.75 … +20.75 mm |
| 2 | Timeline: edit *Bin placement* in the bin's group (or look at its X/Y distance) | X and Y show a formula with `gfBin1_baseWidth` / `gfBin1_baseLength`, no plain number; no feature more than on master |
| 3 | Modify › Change Parameters: `gfBin1_baseWidth` 42 → 50 mm | Bin grows to both sides, X −49.75 … +49.75 mm; foot joint origins at X −25 / +25 mm |
| 4 | Change Parameters: `gfBin1_baseLength` 42 → 46 mm | Y −22.75 … +22.75 mm, still centered |
| 5 | Bin dialog, Snap to free spot, 1 x 1 x 3, OK; then Change Parameters `gfBin2_baseWidth` 42 → 50 mm | Snapped bin keeps its left edge and grows to the right, as before; the centered bin doesn't move |
| 6 | Rebuild the centered bin through its dialog (right click › edit), base width 42 mm, OK | Bin rebuilt centered at 42 mm, no warning, timeline healthy |
| 7 | New bin: 1.5 x 2.5 x 3, half grid, *Center on origin*; then `gfBin3_baseWidth` → 50 mm | Stays centered on the origin |
| 8 | New bin: 2 x 1 x 3, label text and icon raised in a color, *Center on origin*; then its base width → 50 mm | Bin and colored letters stay centered together, the letters on the tab |
| 9 | Close the document without saving | – |
