# Exporting for printing

**Gridkeeper export** writes the parts of a design to files for the slicer: one **3MF** with all of them, or an **STL**
or **STEP** file of each part. It comes from GridfinityGenerator (Le0Michine), Gridkeeper extends it to every part it
builds and to colored text.

## Starting the export

- **Right-click** a bin, baseplate or Cullenect insert, a letter or symbol of one, its component in the browser, or a
  container (*Grid*, *Bins*, *Label*), and pick **Gridkeeper export**. It sits below *Save As Mesh*.
- Right-click the design's root component to start with **All Gridkeeper parts** on.

## The dialog

| Input | What it does |
|---|---|
| **All Gridkeeper parts** | Selects every visible bin, baseplate, Cullenect insert and box of the design. Off goes back to what was selected |
| **Bodies** | What goes out. A selected letter or symbol stands for its part; any other body picked goes out as it is |
| **Format** | **3MF**: one file with all parts, laid out as in the design. **STL** or **STEP**: a file of each part, named after it, at the origin with its bottom at zero |
| **Folder**, **Choose folder...** | Where the files go, the last folder is kept |
| **File name** | Name of the 3MF file, the part's name for one part |
| **Color label text** | 3MF only: the label text gets a color index the slicer prints it in, see below |
| **Label color index** | The slicer's filament for the label text, counting from 1 as the slicer lists them |

Existing files are only replaced after asking. 3MF and STL meshes are made at Fusion's very high quality.

## Which parts

| Part | Exported with |
|---|---|
| Bin | its colored label text and symbol bodies |
| Baseplate | – |
| Cullenect insert | its text and symbol bodies |
| Box and lid (Pred box) | as soon as the box is part of Gridkeeper |

Each part is one object in the 3MF and one STL or STEP file, its text and symbol bodies included, so the part comes
out whole. The text bodies are never a part of their own.

## Colored label text in the 3MF

With **Color label text** on, the triangles of the label text are painted with the **Label color index**, the way the
slicers' paint tool stores it. Bambu Studio, OrcaSlicer and PrusaSlicer print them in that filament without painting
by hand:

- **Outline labels without a color:** the tops of the letters are painted.
- **Colored labels** of bins and the **text and symbols of inserts** (bodies of their own, see
  [Colors and multicolor printing](colors.md)): all their triangles are painted.

All label text gets the same index, whatever color it has in Fusion. Without **Color label text** the text is still in
the file, in the part's filament.

!!! note "Known limits"
    - A bin built as bodies in the root component, without a component of its own, has no *Text* component; its
      colored label bodies are not found and are missing from the export. Rebuild it to get a component.
    - STL and STEP files have no colors. In STEP the text bodies are bodies of their own beside the part.

## In the slicer

1. Open the 3MF in Bambu Studio, OrcaSlicer or PrusaSlicer.
2. Make sure the filament list has a filament at the **Label color index** you picked.
3. Slice and check in the preview that the letters print in that filament.
