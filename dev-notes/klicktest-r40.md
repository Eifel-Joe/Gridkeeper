# Click test round 40: symbols of lines and arcs, one import

Add-in loaded from `wt-r40` (branch `r40-symbol-speed`). A new design for each part unless a step says otherwise.
Times are from pressing OK until the part shows; before this round the Torx symbol took about 40 s.

## Box label

| # | Steps | Expected |
|---|---|---|
| 1 | **Gridkeeper box label**, 5 cells, big text *M4*, line 1 *x16*, symbol 1 *Countersunk Torx/Star*, OK | Built in a second or two. The Torx drive shows six round lobes, smooth, no facets; symbol in the first symbol place |
| 2 | Same label, symbols 1 to 3: *Pan Torx/Star*, *Countersunk Phillips*, a hardware symbol (*Nut nylon*) | Each symbol in its place, height as before, round parts round |
| 3 | Timeline: open the symbol sketch of step 1 | 54 curves (lines and arcs), sketch fully constrained (no blue lines) |
| 4 | Surface *Debossed*, OK | Symbol cut into the plate, edges clean |

## Insert (Cullenect label)

| # | Steps | Expected |
|---|---|---|
| 5 | **Gridkeeper label** 1U, head *Countersunk*, driver *Torx*, text *M3x10*, OK | Built in about a second; symbol at the right edge, Torx lobes round |
| 6 | Head *Pan*, driver *Torx*, flange and security on | Symbol with its security pin as a round dot in the drive |
| 7 | Head *None* (set screw), driver *Hex* | End disc round, hex socket in it |
| 8 | Hardware *Nut nylon*, no screw | Symbol as before (this one stays a polygon) |
| 9 | Change the width parameter of the insert of step 5 (Change Parameters) | Symbol moves along with the right edge |

## Bin label

| # | Steps | Expected |
|---|---|---|
| 10 | **Gridkeeper bin** 2 × 1 × 3, label tab, label icon *Hex nut*, text *M4*, OK | Icon on the tab beside the text, as before |
| 11 | Label icon *Cullenect crimp butt splice* | Icon on the tab, round ends round; build not slower than before |
| 12 | Tab tilted (steep tab), icon *Cullenect washer* | Icon flat on the tilted tab face, not standing on its head |
| 13 | Edit the label text parameter of step 10 to *M4 long* | Text follows, icon stays in place |

## Symbol dropdowns

| # | Steps | Expected |
|---|---|---|
| 14 | Bin dialog, label icon dropdown, light and dark theme | Previews of the Cullenect icons look as before |
