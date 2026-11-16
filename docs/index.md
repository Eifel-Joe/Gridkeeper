# Gridkeeper

Gridkeeper is an add-in for Autodesk Fusion that builds [Gridfinity](https://www.youtube.com/watch?v=ra_9zU-mnl8)
baseplates, bins and exchangeable [Cullenect](https://github.com/CullenJWebb/Cullenect-Labels) label inserts. It is
our further development of [GridfinityGenerator](https://github.com/Le0Michine/FusionGridfinityGenerator) by
Le0Michine (Lev Mishin): everything GridfinityGenerator does is still there, extended by Cullenect label pockets and
inserts, colored labels for multicolor printing, an assembly of components with joints, and a number of fixes and
smaller features, see [What's new](getting-started/whats-new.md).

![A drawer of Gridkeeper bins on a baseplate, some with Cullenect label inserts](assets/images/home-hero.png)

## What it builds

| | |
|---|---|
| **[Baseplates](baseplates.md)** | Plates of sockets for the bins, light, full or skeletonized, with magnets and screws, or a whole drawer filled and split into pieces that fit your print bed. |
| **[Bins](bins/index.md)** | Hollow, shelled or solid bins of any size in whole or half base units, custom shapes, compartments, a scoop, a label tab with text and an icon, magnet and screw holes in the base. |
| **[Cullenect labels](cullenect/index.md)** | Pockets in the label tab of a bin and the label inserts that click into them, with text and a screw or hardware symbol, printed in two colors and swapped when the contents change. |

Every model is parametric and remembers how it was built: right-click it to see its
[settings, to rebuild it or to clone it](working/settings-rebuild-clone.md), or change its
[user parameters](working/parameters.md) without building it again.

## Commands

After [installation](getting-started/installation.md) Gridkeeper adds these commands to Fusion's Design workspace:

| Command | Where | What it does |
|---|---|---|
| **Gridkeeper baseplate** | Solid › Create | Builds a baseplate, see [Baseplates](baseplates.md) |
| **Gridkeeper bin** | Solid › Create | Builds a bin, see [Bins](bins/index.md) |
| **Gridkeeper label** | Solid › Create | Builds a Cullenect label insert, see [Label inserts](cullenect/inserts.md) |
| **Gridkeeper settings** | right-click a generated body | Shows what it was built with, saves, copies or clones it |
| **Gridkeeper rebuild** | right-click a generated body | Opens its dialog to build it again in its place |
| **Gridkeeper clone** | right-click a generated body | Opens its dialog with its settings for a new one |
| **Gridkeeper tests: run** | Utilities › Add-Ins, git checkouts only | Shape snapshot tests for developers, see [Snapshot tests](developers/snapshot-tests.md) |

## Vibe-coded, tested by printing

Gridkeeper is vibe-coded: its code is written by an AI, Claude, under the lead of Eifel-Joe, who designs the features,
tests them in Fusion and prints the results. Every change is checked by automated tests and by real prints. Still,
expect rough edges, and please [report what you find](https://github.com/Eifel-Joe/FusionGridfinityGenerator/issues).

## Credits

- **GridfinityGenerator** by [Le0Michine](https://github.com/Le0Michine/FusionGridfinityGenerator), CC BY-NC-SA 4.0,
  the add-in Gridkeeper is built on
- **Cullenect-Labels** by [CullenJWebb](https://github.com/CullenJWebb/Cullenect-Labels), MIT, the label inserts,
  their pockets and symbols
- **gridfinity_extended_openscad** by [ostat (Chris Heazlewood)](https://github.com/ostat/gridfinity_extended_openscad),
  used as a reference
- **Gridfinity** by [Zack Freedman](https://www.youtube.com/c/ZackFreedman/about)

Gridkeeper is licensed under [CC BY-NC-SA 4.0](http://creativecommons.org/licenses/by-nc-sa/4.0/), see
[Credits and license](reference/credits.md).
