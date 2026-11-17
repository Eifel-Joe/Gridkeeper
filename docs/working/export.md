# Exporting for printing

**Gridkeeper export** writes the parts of a design to files for the slicer: one **3MF** with all of them, or an **STL**
or **STEP** file of each part. It comes from GridfinityGenerator (Le0Michine), Gridkeeper extends it to every part it
builds and to colored text.

## Starting the export

- **Right-click** a bin, baseplate, Cullenect insert or storage box, a letter or symbol of one, its component in the
  browser, or a container (*Grid*, *Bins*, *Label*, *Boxes*), and pick **Gridkeeper export**. It sits below *Save As Mesh*.
- Right-click the design's root component to start with **All Gridkeeper parts** on.

![The right-click menu of a bin's component with Gridkeeper export below Save As Mesh, and settings, rebuild and clone at the end](../assets/images/context-menu-export-scene.png)

## The dialog

| Input | What it does |
|---|---|
| **All Gridkeeper parts** | Selects every visible bin, baseplate, Cullenect insert and box with its small parts of the design. Off goes back to what was selected |
| **Bodies** | What goes out. A selected letter or symbol stands for its part; any other body picked goes out as it is |
| **Format** | **3MF**: the parts in print orientation laid out on the print bed, a file per plate, see below. **STL** or **STEP**: a file of each part, named after it (a box's *Base*, *Lid* and small parts with the box's name in front, such as *Box 5×4×6 Base*, *Box 5×4×6 Latch*), at the origin with its bottom at zero. STL files come in print orientation, STEP files as designed |
| **Folder**, **Choose folder...** | Where the files go, the last folder is kept |
| **File name** | Name of the 3MF file, the part's name for one part; with several plates *, plate 1*, *, plate 2* … is added |
| **Color label text** | 3MF only: the label text gets a color index the slicer prints it in, see below |
| **Label color index** | The slicer's filament for the label text, counting from 1 as the slicer lists them |
| **Print bed** › **Printer** | 3MF only: your printer, see [Choosing the printer](#choosing-the-printer); its bed size, where its slicer puts the purge tower and the area it keeps free come with it |
| **Bed width, X**, **Bed length, Y** | The bed's usable size; typing a size switches the printer to *Custom* |
| **Spacing** | Space between the parts and to the bed's edge, 5 mm to start with |
| **Purge tower area** | With **Color label text** on and text to color: a square kept free on every plate for the purge tower, 50 mm to start with, 0 for none |

The dialog keeps its choices for the next export. Existing files are only replaced after asking. 3MF and STL meshes are made at Fusion's very high quality.

## Choosing the printer

**Print bed › Printer** tells the export which bed to lay the parts out on. Pick your printer, or *Custom* and type
**Bed width, X** and **Bed length, Y** yourself. The list is the same as in the baseplate dialog:

| Printer | Bed (mm) | Purge tower square, with colored text | Kept free |
|---|---|---|---|
| Bambu Lab A1 mini | 180 × 180 | back left | – |
| Bambu Lab A1 | 256 × 256 | back left | – |
| Bambu Lab A2L | 330 × 320 | back left | – |
| Bambu Lab P1P, P1S, X1, X1C, X1E | 256 × 256 | back, at about two thirds of the width | front left 18 × 28 mm, where the nozzle is wiped |
| Bambu Lab P2S, X2D | 256 × 256 | back, at about two thirds of the width | – |
| Bambu Lab H2C | 330 × 320 | back, at about two thirds of the width | – |
| Bambu Lab H2D, H2D Pro | 350 × 320 | back, at about two thirds of the width | – |
| Bambu Lab H2S | 340 × 320 | back, at about two thirds of the width | – |
| Bambu Lab H3C | 330 × 320 | front right | – |
| Prusa MINI, MK3/MK4, CORE One, XL; Creality Ender-3, K1/K1C, K1 Max; Elegoo Neptune 4; Voron 0, 250, 300, 350 | the printer's bed | back right | – |
| *Custom* | as typed | back right | – |

For the Bambu Lab printers the purge tower square and the area kept free come from Bambu Studio's own printer
profiles, so the slicer's purge tower lands on the free square without moving it and no collision warning comes up.
For every other printer and *Custom* the square is at the back right: move the slicer's purge tower onto it, and mind
any area your printer keeps free yourself. Typing a bed size switches the printer to *Custom*.

## Which parts

| Part | Exported with |
|---|---|
| Bin | its colored label text and symbol bodies |
| Baseplate | – |
| Cullenect insert | its text and symbol bodies |
| Box and lid (Pred box) | – |
| Small parts of a box: latches, handle, handle pins, hinges | – (each placed one is a part of its own: the four latches give four files) |

Each part is one object in the 3MF and one STL or STEP file, its text and symbol bodies included, so the part comes
out whole. The text bodies of a part in its own component are never a part of their own.

## Print orientation and layout in the 3MF

Every part of the 3MF lies the way it is printed, whatever its place in the design:

| Part | Lies on the bed |
|---|---|
| Bin, baseplate | standing, as designed |
| Cullenect insert, box label | on its underside, as it is built in; a **Flush** insert on its text |
| Box | on its bottom |
| Lid | as it sits on the box |
| Latch | flat |
| Handle | flat, 7 mm high |
| Handle pin | on its flat side |
| Hinge | standing, both halves together as printed; the pin of the *Pinned* hinge on its flat side |

The print orientation of the box's parts follows
[Pred's storage box](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric) (CC BY-NC).

The parts are then laid out in rows, the largest first, with the **Spacing** between them and to the edge, as a
compact, roughly square group in the middle of the bed rather than across its whole width; the rows only widen when
that saves a plate. A part that only fits across is turned by 90°. What doesn't fit goes on further plates, and **each plate is a
3MF file of its own**: *Gridkeeper parts, plate 1.3mf*, *Gridkeeper parts, plate 2.3mf* and so on, just *Gridkeeper
parts.3mf* when one plate holds all. A part larger than the bed lies alone on a plate of its own and is named in the
message after the export. Plate files of an earlier export of the same name that the new one doesn't write are
removed, after asking together with the files it replaces.

With **Color label text** on and label text to color, a square stays free for the purge tower on every plate. For a
Bambu Lab printer it lies where Bambu Studio puts the tower (from its printer profiles): at the back, at about two
thirds of the width, for the P1, X1, P2S, X2D and H2 printers; back left for the A1, A1 mini and A2L; front right for
the H3C. For the other printers and *Custom* it is the back right corner: move the slicer's purge tower there. The
message names a plate where the square couldn't be kept free, a box as wide as the bed for one.

A storage box set goes on plates of its own: the box on one, the lid on one, the latches, handle, pins and hinges on
a third, more if they don't fit. Other parts exported with it share their own plates.

With a Bambu Lab printer chosen, the area it keeps free stays free too: the **P1P, P1S, X1, X1C and X1E** wipe the
nozzle in the front left corner (18 × 28 mm), and Bambu Studio warns of collisions when a part comes near it. A large
part such as a box then fills its plate alone. The message names a plate where a part couldn't keep clear. With
*Custom* or another printer such areas are yours to mind.

The parts of each file are centered on the bed: Bambu Studio, OrcaSlicer and PrusaSlicer move the parts of a 3MF made
elsewhere to the middle of the bed as a group, so the layout stays as it is when the file is opened. Don't press
**Arrange** in the slicer, it would spread them anew. A file per plate works in every slicer without changing its
printer, filament or process settings; a 3MF with several plates in one file would have to bring the slicer's own
project settings along.

## Colored label text in the 3MF

With **Color label text** on, the triangles of the label text are painted with the **Label color index**, the way the
slicers' paint tool stores it. Bambu Studio, OrcaSlicer and PrusaSlicer print them in that filament without painting
by hand:

- **Outline labels without a color:** the tops of the letters are painted.
- **Colored labels** of bins and the **text and symbols of inserts** (bodies of their own, see
  [Colors and multicolor printing](colors.md)): all their triangles are painted.

In the file the index is written the way the slicers' paint tool codes it, not as a plain number: filament 1 is `4`,
filament 2 is `8`, from filament 3 on `0C`, `1C`, … (in `paint_color`, `slic3rpe:mmu_segmentation` and PrusaSlicer's
`Metadata/Slic3r_facets_annotation.json`). The slicer shows it as the filament number you picked.

All label text gets the same index, whatever color it has in Fusion. Without **Color label text** the text is still in
the file, in the part's filament.

!!! note "Known limits"
    - A bin built as bodies in the root component, without a component of its own (older designs), has no *Text*
      component; its colored label bodies are not found and are missing from the export. A rebuild keeps it in the
      root; **Gridkeeper clone** builds a copy in a component of its own, then delete the old bin.
    - An insert in the root component exports its text and symbol bodies as parts of their own, unpainted. Clone it
      into a component the same way.
    - STL and STEP files have no colors. In STEP the text bodies are bodies of their own beside the part.

## In the slicer

1. Open the 3MF in Bambu Studio, OrcaSlicer or PrusaSlicer.
2. Make sure the filament list has a filament at the **Label color index** you picked.
3. Slice and check in the preview that the letters print in that filament.
