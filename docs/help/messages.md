# Messages and locked OK

Gridkeeper tells you in four ways that something doesn't work: **OK** stays greyed out (the dialog shows why where it
can), a message after building, the **Gridfinity error** panel when a build fails, and notes after a rebuild. This
page lists them all, with what to do.

## OK stays locked

| Dialog | Message or reason | What to do |
|---|---|---|
| Bin | **Cullenect: Cullenect sockets need walls of at least 1.2 mm** (in the Actual dimensions table) | Set **Bin wall thickness** to 1.2 mm or more, or pick another label style |
| Bin | **Pick at least one cell** (custom shape drawing) | Click at least one cell, or untick **Custom shape** |
| Bin | **All cells must form one piece, joined along their sides** | Cells touching only at a corner don't count; connect them |
| Bin | A **Custom label color** that isn't `#rrggbb` | Type a color like `#D02020` |
| Bin | A value out of its range: base units over 10 mm, height unit over 5 mm, xy clearance 0.1 to 0.5 mm, width and length in half units, height at least 1, wall 0.4 to 2 mm, tab overhang 30° to 65°, tab top 0° to 45°, socket play 0 to 1 mm, a screw hole over 1 mm and smaller than the magnet socket | Correct the value; Fusion shows it red |
| Baseplate | **Base units must be greater than 0**, **Plate size must be at least 1 x 1 u** (in Result) | Correct the size |
| Baseplate | **The area is too small to fit a single cell** | Make the area larger than one cell plus clearance |
| Baseplate | **The print bed is too small to fit a single cell with the side padding** | Pick a larger bed, a smaller bed margin or less padding |
| Baseplate | Clearances out of range, magnet over 10 mm, screw hole over 10 mm, screw head not larger than the screw hole or over 15 mm, connection hole over 5 mm | Correct the value |
| Label | **An insert is 10 to 300 mm wide** | Change the width or the correction |
| Label | **An insert is at least 5 mm high** | Make the height correction smaller |
| Label | **Corrections are at most 1 mm either way** | Keep both corrections between −1 and 1 mm |
| Label | **The base width unit is at least 10 mm** | Correct **Base width unit (mm)** |
| Label | **No room for the symbol, make the insert wider** | Wider insert, or no symbol |
| Label | **No room for text beside the symbol, make the insert wider** | Wider insert, or no symbol |
| Label | **Two lines don't fit this height: their descenders would reach over the edge and the letters can't get smaller without getting too thin to print. Make the height correction smaller, use one line or the Heavy style** | As the message says |
| Label | **No svg for this symbol** | The chosen combination has no symbol file; pick another (only happens with symbol folders changed by hand) |
| Label | **This pocket is too small for the insert, pick one that fits** | Pick a larger pocket or make the insert narrower |
| Label | A **Custom color** that isn't `#rrggbb` | Type a color like `#D02020` |

## Messages after building

| Message | Meaning |
|---|---|
| **This document was a part design. It has been switched to a hybrid design, so the bin is a component of its own. A design holding components can no longer be switched back to a part design.** | Shown once, when the first model is built in a part design. See [Components and joints](../working/components.md#part-designs). |
| **"M3": 2.8 mm high, below the 3.05 mm a 0.4 mm nozzle prints in Heavy. Shorten the text, make it wider or use the Heavy style.** (insert) | The text was fitted below the print limit of its style, a 0.4 mm nozzle will leave parts of the letters out. The insert is built anyway. |
| **"…": … mm high, below the … mm a 0.4 mm nozzle prints in Regular. Make the tab wider or use the Bold style.** (bin) | Only on a tab lower than the print limit. The bin is built anyway. |
| **Loaded "file.json" with changes:** followed by *Not recognised, skipped*, *Not in the file, kept the current value*, *Unknown option, used the default* | A settings file of another version, see [Saving and loading settings](../working/save-load.md#loading-older-or-other-files). |

The preview shows the thin text note too: **Last preview** gets ", text below the print limit".

## Build failed: the Gridfinity error panel

When a build fails, a panel **Gridfinity error** stays open with the error, the stack trace and the settings it was
built from (and, for a rebuild, the settings before). **Copy report** copies all of it for a bug report, **Copy and
open an issue** also opens the issue page.

Errors you can fix yourself:

| Error | What to do |
|---|---|
| **"…" doesn't fit the label even at 4.4 mm, the least height a 0.4 mm nozzle prints. Shorten it or make the bin wider.** | A bin label text too long for its tab, see [Text size](../bins/labels.md#text-size). A longer **Tab length** also helps. |
| **"…" doesn't fit the label even at … mm, as high as its tab lets it be. Shorten it or make the bin wider.** | The same on a tab lower than the print limit. |
| **Timeline must be enabled for the generator to work, projects with disabled design history currently are not supported** | Turn on **Capture Design History** (right-click the document root in the browser). |

## Rebuild

| Message | Meaning |
|---|---|
| **The bin was rebuilt. These features after it need a look, ones using a face or an edge of the old bin need them picked again:** and a list | Open each listed feature in the timeline and pick its faces or edges again. Same for baseplates and inserts. |
| **…: the insert doesn't fit the rebuilt … any more, … x … mm into … x … mm** (in that list) | A pocket of the rebuilt bin became smaller than the insert jointed into it. Rebuild the insert narrower. |
| **The pocket the insert was in, …, couldn't be picked. Pick it again, otherwise the insert is built where it was without a joint.** (label dialog) | Pick the pocket's joint origin in **Pocket** again. |
| **The bin of this pocket comes after the insert in the timeline, the insert can't be rebuilt into it in place** | The insert is older than the bin; build a new insert into the pocket instead. |
| **Rebuilding needs the design history, the timeline, turned on** | Turn on **Capture Design History**. |
| **The timeline group … was generated in wasn't found, it may have been ungrouped** / **No generated bodies were found in the timeline group …** | The timeline group of the model was taken apart or emptied; Gridkeeper can't find what to replace. Use **Gridkeeper clone** to build a new one. |
| **The body to rebuild is no longer in the design** | The body was deleted after the menu opened. |
| **Select a generated bin, baseplate or label to rebuild.** / **… to clone.** | The selection isn't a Gridkeeper model; select its body. |

## Settings files

| Message | Meaning |
|---|---|
| **Couldn't read the config. It isn't a JSON file, …** | The file isn't valid JSON. |
| **… It's the config of a baseplate, not of a bin** | A file of another generator. |
| **… binWidth has to be a number, not "two"** | A setting of the wrong type; the file is refused as a whole. |
| **Couldn't save the config to …** / **Couldn't read …** / **Couldn't copy to the clipboard** | A file or clipboard error from the system. |
