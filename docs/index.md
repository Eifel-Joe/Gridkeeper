# Gridkeeper

Gridkeeper is an add-in for Autodesk Fusion that builds [Gridfinity](https://www.youtube.com/watch?v=ra_9zU-mnl8)
baseplates, bins, exchangeable [Cullenect](https://github.com/CullenJWebb/Cullenect-Labels) label inserts and storage
boxes with a lid. It is our further development of
[GridfinityGenerator](https://github.com/Le0Michine/FusionGridfinityGenerator) by Le0Michine (Lev Mishin): everything
GridfinityGenerator does is still there, extended by Cullenect label pockets and inserts, storage boxes after Pred,
colored labels for multicolor printing, an assembly of components with joints, an export for the slicer, and a number
of fixes and smaller features, see [What's new](getting-started/whats-new.md).

![Three Gridkeeper bins on a baseplate, with labels and symbols in red and blue](assets/images/home-hero.png)

## What it builds

| Model | What it is |
|---|---|
| **[Baseplates](baseplates.md)** | Plates of sockets for the bins, light, full or skeletonized, with magnets and screws, or a whole drawer filled and split into pieces that fit your print bed. |
| **[Bins](bins/index.md)** | Hollow, shelled or solid bins of any size in whole or half base units, custom shapes, compartments, a scoop, a label tab with text and an icon, magnet and screw holes in the base. |
| **[Cullenect labels](cullenect/index.md)** | Pockets in the label tab of a bin and the label inserts that click into them, with text and a screw or hardware symbol, printed in two colors and swapped when the contents change. |
| **[Storage boxes](boxes.md)** | A box with a lid after Pred's parametric Gridfinity Storage Box: bins sit in its floor, its lid carries a grid or a closed top, with latches, handle and hinges, and a label for the holder at the front. Stacks and latches with boxes printed from Pred's own file. |

Every model is parametric and remembers how it was built: right-click it to see its
[settings, to rebuild it or to clone it](working/settings-rebuild-clone.md), or change its
[user parameters](working/parameters.md) without building it again. [Export](working/export.md) writes all parts
into one 3MF for the slicer, label colors included.

## Commands

After [installation](getting-started/installation.md) Gridkeeper adds these commands to Fusion's Design workspace:

| Command | Where | What it does |
|---|---|---|
| **Gridkeeper baseplate** | Solid › Create | Builds a baseplate, see [Baseplates](baseplates.md) |
| **Gridkeeper bin** | Solid › Create | Builds a bin, see [Bins](bins/index.md) |
| **Gridkeeper label** | Solid › Create | Builds a Cullenect label insert, see [Label inserts](cullenect/inserts.md) |
| **Gridkeeper box** | Solid › Create | Builds a storage box with a lid, see [Storage boxes](boxes.md) |
| **Gridkeeper box label** | Solid › Create | Builds the label for the holder at the front of a box, see [Label](boxes.md#label) |
| **Gridkeeper settings** | right-click a generated body | Shows what it was built with, saves, copies or clones it |
| **Gridkeeper rebuild** | right-click a generated body | Opens its dialog to build it again in its place |
| **Gridkeeper clone** | right-click a generated body | Opens its dialog with its settings for a new one |
| **Gridkeeper export** | right-click a generated body | Writes the parts to a 3MF, STL or STEP file, see [Export](working/export.md) |
| **Gridkeeper updates** | Utilities › Add-Ins | Shows the running and the newest version and updates Gridkeeper, see [Installation](getting-started/installation.md) |
| **Gridkeeper tests: run** | Utilities › Add-Ins, git checkouts with a `.git` folder only | Shape snapshot tests for developers, see [Snapshot tests](developers/snapshot-tests.md) |

## Vibe-coded, tested by printing

Gridkeeper is vibe-coded: its code is written by an AI, Claude, under the lead of Eifel-Joe, who designs the features,
tests them in Fusion and prints the results. Every change is checked by automated tests, by shape tests in Fusion and
by clicking through the dialogs; prints follow. Still,
expect rough edges, and please [report what you find](https://github.com/Eifel-Joe/Gridkeeper/issues).

## Credits

- **GridfinityGenerator** by [Le0Michine](https://github.com/Le0Michine/FusionGridfinityGenerator), CC BY-NC-SA 4.0,
  the add-in Gridkeeper is built on
- **Cullenect-Labels** by [CullenJWebb](https://github.com/CullenJWebb/Cullenect-Labels), MIT, the label inserts,
  their pockets and symbols
- **Gridfinity Storage Box v1.1 (parametric)** by
  [Pred](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric), CC BY-NC, the shape
  of the storage box, its lid and small parts, rebuilt in code
- **gridfinity_extended_openscad** by [ostat (Chris Heazlewood)](https://github.com/ostat/gridfinity_extended_openscad),
  used as a reference
- **Gridfinity** by [Zack Freedman](https://www.youtube.com/c/ZackFreedman/about)

Gridkeeper is licensed under [CC BY-NC-SA 4.0](http://creativecommons.org/licenses/by-nc-sa/4.0/), see
[Credits and license](reference/credits.md).
