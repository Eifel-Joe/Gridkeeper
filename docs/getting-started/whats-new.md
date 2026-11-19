# What's new compared to GridfinityGenerator

Gridkeeper starts from GridfinityGenerator v2.4.2.0 by Le0Michine, takes over its later changes (such as the lip
types) and keeps all of it: baseplates that fill an area and split it for the print bed, bins of custom shapes with
compartments, scoops and label tabs, creased walls, rebuilding and cloning from the right-click menu, settings saved
to JSON files. On top of that it adds the following.
The full list of changes, round by round, is in
[CHANGELOG.md](https://github.com/Eifel-Joe/Gridkeeper/blob/master/CHANGELOG.md).

## Storage boxes

- **Gridkeeper box:** a storage box with lid after [Pred's parametric Gridfinity Storage Box v1.1](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric)
  (CC BY-NC), rebuilt in code
  with fully constrained sketches: any size from 4 × 3 cells and 6 units, stacking and latching with Pred's printed
  boxes, size parameters `gfBox1_…`, joint origins in the floor, for stacking and for the lid. See
  [Storage boxes](../boxes.md).
- **Magnet size** to choose in the bin and baseplate dialogs: 6 × 2 or 6 × 3 mm magnets set the depth. The box takes
  6 × 2 mm magnets only, 6 × 3 mm ones would break through its floor.

## Cullenect labels

- **Cullenect label style for bins:** the label tab, or every compartment tab, gets a pocket for an exchangeable
  [Cullenect](https://github.com/CullenJWebb/Cullenect-Labels) label insert instead of a printed label, sized to the
  widest standard Cullenect width that fits, so original Cullenect inserts fit too. See
  [Pockets in bins](../cullenect/pockets.md).
- **Gridkeeper label**, a command of its own for the inserts: one or two lines of text and a screw or hardware symbol,
  raised, set in or flush, as bodies of their own for a second color. See [Label inserts](../cullenect/inserts.md).
- **Symbols:** 480 screw combinations of head, shaft, threads, driver, flange and security pin, set screws, and 18
  hardware symbols (washers, nuts, T-nuts, threaded insert, magnet, crimp terminals), drawn from Cullenect's own
  code. New svg files in the symbol folders show up in the dialog. See [Symbols](../cullenect/symbols.md).
- **Inserts jointed into their pockets:** every pocket has a joint origin; pick it in the label dialog and the insert
  sits in the pocket. A rebuilt bin keeps its inserts in their pockets.
- **Inserts like bins:** inserts are rebuilt, cloned, saved and loaded the same way as bins and baseplates.

## Labels and colors

- **Label color** for bin labels and **Text color** for inserts: the letters and symbols become bodies of their own
  in a color, ready for a multicolor print; an exported 3MF has each in its color. See
  [Colors and multicolor printing](../working/colors.md).
- **Text styles for inserts:** Regular, Bold and Heavy (Arial Black). Heavy prints cleanly with a 0.4 mm nozzle and is
  the default.
- **Printable text heights:** a bin label text is never shrunk below the height where its thinnest stroke is still
  one 0.4 mm nozzle line (Regular 4.43 mm, Bold 3.42 mm, measured); inserts tell you after building when their text
  is below it (Heavy 3.05 mm).
- **Hardware symbols on bin labels:** the Cullenect hardware symbols can be picked as label icons of normal bins too.
- **Labels follow their text:** a bin label text changed through its user parameter follows the tab, new letters get
  the label color, and **Gridkeeper rebuild** fits a longer text to the tab again.

## Bins

- **Dividers up to the top on grid lines:** compartment dividers on a grid line reach the top of the lip; the feet of a
  bin stacked on top have a groove there, so bins of any size still stack.
- **Joint origins follow the grid:** the joint origins of bin feet and baseplate sockets move with the base unit
  parameters.
- **Cullenect walls:** a bin with Cullenect pockets needs walls of at least 1.2 mm, the dialog says so instead of
  building a weak tab.

## Export

- **Gridkeeper export** in the right-click menu, from GridfinityGenerator (Le0Michine): one 3MF of all parts with the
  label text painted for Bambu Studio, OrcaSlicer and PrusaSlicer, or an STL or STEP file each. Gridkeeper exports
  Cullenect inserts too and puts the colored text and symbol bodies of bins and inserts into their part, painted. See
  [Exporting for printing](../working/export.md).
- **Print orientation:** the 3MF lays every part the way it is printed, the box's handle and latches flat, and
  spreads them over the chosen print bed with spacing, a 3MF per plate if one isn't enough, with the corner for the purge
  tower kept free.
- From GridfinityGenerator too: the letters of outline labels show in a color of their own in Fusion, the bin dialog
  shows the bin's size to the micron, and baseplates set the **Plate edge clearance** per edge (older settings are
  read as half the old gap).

## Updates

- **Update check:** once a day at startup Gridkeeper asks GitHub for a new version and shows it with a link to its
  release notes; **Update now** replaces the add-in folder, keeping your dialog defaults. Git checkouts are never
  replaced, and the check can be turned off. See [Update](installation.md#update).

## The design

- **An assembly of components:** every baseplate, bin and insert is a component of its own, in the containers
  *Grid*, *Bins* and *Label*. Colored letters are in a *Text* component inside, so they export apart. A part design is
  switched to a hybrid design for this. See [Components and joints](../working/components.md).
- **The root stays active** after a build, Fusion doesn't show everything else half transparent.

## Credits and naming

- The commands are called **Gridkeeper bin**, **Gridkeeper baseplate**, **Gridkeeper label**, **Gridkeeper
  settings**, **Gridkeeper rebuild**, **Gridkeeper clone** and **Gridkeeper export**, so they don't mix with the original add-in. Bodies are
  still named *Gridfinity bin …*, as before.
- Installed from the ZIP of a GitHub release, not from the Autodesk App Store, see
  [Installation](installation.md).
