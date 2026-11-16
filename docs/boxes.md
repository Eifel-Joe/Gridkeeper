# Storage boxes

**Solid › Create › Gridkeeper box** builds a storage box with a lid after
[Pred's parametric Gridfinity Storage Box v1.1](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric)
(CC BY-NC). The box holds Gridfinity bins in its floor, carries a Gridfinity grid on its lid, and stacks and latches
with boxes printed from Pred's own file: outer size, grooves, latch catches, hinge slots, handle and label holders
and the stacking rim are Pred's to the millimetre.

Every new box is a component of its own in the container *Boxes*, holding the components *Box* and *Lid*; the lid
is jointed shut on the box, see [Components and joints](working/components.md).

!!! note "This round builds box and lid"
    The latches, hinges, handle with its pins and the label come in the next versions. Box and lid already have
    every seat for them.

## Info

A link to this page, the credit to Pred and the version of the add-in. When the dialog was opened by
**Gridkeeper rebuild**, it says which box is rebuilt in place.

## Size

| Input | Default | What it does |
|---|---|---|
| **Width (u)** | 5 | Grid cells of 42 mm across, at least 4 |
| **Length (u)** | 4 | Grid cells of 42 mm from front to back, at least 3 |
| **Height (u)** | 6 | Height units of 7 mm, at least 6 like Pred; the lid adds 10 mm |

The line below shows the outer size: width and length are the cells plus a 10 mm rim on every side
(5 × 4 → 230 × 188 mm).

## Magnet holes

| Input | Default | What it does |
|---|---|---|
| **Add magnet holes** | off | A hole in the pad at each corner of every cell |
| **Magnet size** | 6×2 mm (2.4 mm deep) | Sets the depth for 6 × 2 mm magnets, or *Custom* to type it |
| **Magnet cutout depth** | 2.4 mm | Up to 2.6 mm: the pad under the hole is 2.8 mm thick, 6 × 3 mm magnets would go through the floor |
| **Magnet cutout diameter** | 6.5 mm | 3 to 8.5 mm, the pad around the hole grows with it |

## Joint origins

**Add joint origins** puts a joint origin in every cell of the floor, *Cell joint origin column-row*, to joint bins
into the box like onto a baseplate. These are always there:

| Joint origin | Where |
|---|---|
| *Stack bottom joint origin* | Middle of the box's underside |
| *Stack top joint origin* | Middle of the lid's top: joint the bottom of another box onto it to stack them |
| *Lid joint origin* | In box and lid at the middle of the joint between them, used by the joint *Lid on box* |

*Lid on box* is part of the box: a rebuild makes it anew as a rigid joint, changes of yours to it are not kept.

## Parameters

The size is in three user parameters, see [Changing parameters](working/parameters.md):

| Parameter | What it is |
|---|---|
| `gfBox1_baseWidth` | Width in grid cells |
| `gfBox1_baseLength` | Length in grid cells |
| `gfBox1_heightU` | Height in height units |

Change them in **Modify › Change Parameters**, box and lid follow. The joint origins in the floor keep the cells
the box was built with; **Gridkeeper rebuild** places them anew.

## Settings, rebuild and clone

Right-click the box or the lid for the settings, **Gridkeeper rebuild** and **Gridkeeper clone**, see
[Settings, rebuild and clone](working/settings-rebuild-clone.md). A rebuild replaces box and lid together; joints of
yours on its joint origins move over to the joint origins of the same name.

## Credits

Pred's Gridfinity Storage Box v1.1 is licensed CC BY-NC. Gridkeeper rebuilds its box and lid in code, with fully
constrained sketches and parameters, and changes it where noted on this page (the magnet holes, the floor pads and
the stacking rim drawn from circles, the joint origins).
