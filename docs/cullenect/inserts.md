# Label inserts

**Solid › Create › Gridkeeper label** builds a Cullenect label insert: up to two lines of text and a screw or
hardware symbol at its right edge. Every insert is a component of its own in the container *Label*.

![The top of the Gridkeeper label dialog: Info, Size and Text](../assets/images/dialog-label.png)

## Info

Help and the Cullenect credit. When the dialog was opened by **Gridkeeper rebuild**, it says which insert is rebuilt
in place.

## Size

| Input | Default | What it does |
|---|---|---|
| **Width** | Base units | *Base units* or *Width in mm* |
| **Width (u)** | 1 | Shown with *Base units*: width of the pocket it goes into, 0.5 to 7 base units in half steps; 1u is 36 mm with 42 mm units, like Cullenect |
| **Width** (in mm) | 25 mm | Shown with *Width in mm*: a free width, 10 to 300 mm, e.g. for the pocket of a compartment tab; the bin dialog shows its insert width |
| **Base width unit (mm)** | 42 mm | The grid of the bins the width in base units is counted in; with *Base units* only |
| **Correction width** | 0 mm | Added to the width, for printers printing too wide or too narrow, Cullenect's `offset_xy`, at most 1 mm either way |
| **Correction height** | 0 mm | Added to the height of 11 mm, at most 1 mm either way |
| **Insert** | | Shows the size the insert will have, e.g. `36.00 x 11.00 mm`, and in red why it can't be built |

## Text

| Input | Default | What it does |
|---|---|---|
| **Line 1** | M3x10 | First line of text |
| **Line 2** | empty | Second line; with two lines both are set smaller |
| **Text style** | Heavy | *Regular*, *Bold* or *Heavy*. Heavy is Arial Black, its strokes print with a 0.4 mm nozzle. Regular and Bold are Arial, thin when small |
| **Text and symbol** | Raised | *Raised* 0.4 mm, *Set in* 0.4 mm, or *Flush*, see below |
| **Text color** | None | A color for text and symbol, see [Colors and multicolor printing](../working/colors.md) |
| **Custom color** | | Shown for *Text color* *Custom*: `#rrggbb`, e.g. `#D02020` |

Text and symbol are always bodies of their own, two layers (0.4 mm) thick, to print them in another color:

- **Raised** stands 0.4 mm above the insert.
- **Set in** is cut 0.4 mm into the insert; the text body fills the cut and stays hidden, show it to print it in color.
  A set in symbol keeps 0.4 mm off the edges, so the latch still holds.
- **Flush** is cut in the same way and the text body is shown, flush with the face.

![Three inserts with the text and symbol in red: flush, set in (its text body shown) and raised](../assets/images/insert-surfaces.png)

### Text size

The text is fitted to the insert when it is built: one line up to 5 mm high, two lines up to 3.5 mm each, smaller
when long. It keeps 1 mm of room to the right edge and before the symbol, so an insert made up to 1 mm narrower later
still holds it.

A long text is shrunk until it fits. Below the height where its thinnest stroke is one 0.4 mm nozzle line (Regular
4.43 mm, Bold 3.42 mm, Heavy 3.05 mm, measured) a slicer starts leaving parts of the letters out; after building, a
message then suggests to shorten the text, make the insert wider or use the Heavy style.

Two lines on an insert made lower by its height correction shrink so that descenders (g, j, p, y) stay on the
insert, but not below that print limit; where that isn't enough, and where the symbol leaves no room for text, the
dialog says so and **OK** stays locked.

## Symbol

| Input | Default | What it does |
|---|---|---|
| **Screw** | on | A screw put together from head, shaft, threads and driver, at the right edge |
| **Head**, **Shaft**, **Threads**, **Driver** | Socket, Machine, Full, Hex | The parts of the screw; locked without **Screw** |
| **Flange**, **Security pin** | off | Locked where no symbol has them |
| **Hardware** | None | A washer, nut, insert, magnet or crimp terminal instead of a screw; untick **Screw** to pick it |
| **Symbol** | | Shows the svg file of the symbol, *None*, or *No svg for this symbol* |

See [Symbols](symbols.md) for all choices.

## Pocket

Optional: click the joint origin of a Cullenect pocket of a bin, and the insert is jointed into it, flush and
centered. An insert wider or higher than that pocket isn't built, the dialog asks for a pocket that fits. Without a
pocket the insert goes beside the bins, baseplates and inserts there are.

When an insert in a pocket is rebuilt, its pocket is picked again already. If Fusion refuses it, the dialog says so;
pick it again, otherwise the insert is built where it was without a joint.

## Inputs and preview

**Inputs** holds the buttons for defaults and settings files, see [Saving and loading settings](../working/save-load.md).
**Show preview (slow)** builds the insert while you change the inputs; **Last preview** shows how long it took.

## After building

The width and the text lines are [user parameters](../working/parameters.md) of the insert: `gfLabel1_width`,
`gfLabel1_text1` and `gfLabel1_text2`, and with a width in base units `gfLabel1_baseWidth`. The symbol stays at the
right edge when the width changes. A text made longer through its parameter isn't fitted again: it runs on to the
right, shorten it or rebuild the insert.
