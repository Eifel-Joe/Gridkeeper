# Size and shape

## Info

**Info** has a link to this part of the documentation and the version of the add-in; when it was opened by **Gridkeeper rebuild**, it says which bin is rebuilt in place.

## Basic sizes

| Input | Default | What it does |
|---|---|---|
| **Base width unit (mm)** | 42 mm | Size of one grid cell along X, at least 10 mm |
| **Base length unit (mm)** | 42 mm | Size of one grid cell along Y, at least 10 mm |
| **Bin height unit (mm)** | 7 mm | One unit of height, at least 5 mm |
| **Bin xy clearance (mm)** | 0.25 mm | Gap on each side between the bin and its cell, 0.1 to 0.5 mm. Keep it the same as the baseplate's |

Each bin keeps its units as [user parameters](../working/parameters.md) of its own, so changing one bin changes no
other.

## Main dimensions

| Input | Default | What it does |
|---|---|---|
| **Bin width, X (u)** | 2 | In whole or half base units, 0.5 to 100 |
| **Bin length, Y (u)** | 3 | In whole or half base units, 0.5 to 100 |
| **Half grid** | off | Puts the bin on half size feet, for a half grid baseplate; the bin keeps its size in base units |
| **Bin height, Z (u)** | 5 | Total height in height units, base included, at least 1; the stacking lip adds 3.8 mm on top, 4.4 mm with **Trim lip top** off |
| **Custom shape** | off | Shows a drawing of the bin cells to leave some out |

### Actual dimensions

At the end of the section, the **Actual dimensions (mm)** table shows the outer width, length and height the bin will
have. With the Cullenect label style a second row lists the pocket sizes and the insert width that fits each, e.g.
`Cullenect: 2U: pocket 78.3 mm, insert 78 mm`, see [Pockets in bins](../cullenect/pockets.md).

### Half sizes and half grid

A size ending in a half without **Half grid** gets whole feet and a row of half feet along the back or right side,
halved across the row only. With **Half grid** every foot is a half one, so the bin can sit offset by half a cell on a
half grid baseplate. Half feet have no magnet or screw holes, there is no room for them.

<picture><source media="(prefers-color-scheme: dark)" srcset="../../assets/gif/bin-half-grid-dark.gif"><img src="../../assets/gif/bin-half-grid-light.gif" alt="Turning on half grid, then a size ending in a half, with bins on whole, half and a row of half bases"></picture>

### Custom shape

Tick **Custom shape** and click cells in the drawing to leave them out, for a bin shaped like an L, a T or any other
tetris piece. **Fill all** puts every cell back; unticking **Custom shape** fills every cell again.

<picture><source media="(prefers-color-scheme: dark)" srcset="../../assets/gif/bin-custom-shape-dark.gif"><img src="../../assets/gif/bin-custom-shape-light.gif" alt="Drawing a bin shape, with the bin on every cell, then cells left out"></picture>

Compartments, scoop and label tab are not built for custom shapes yet, so a shaped bin has a single compartment and
no label tab or Cullenect pocket.
