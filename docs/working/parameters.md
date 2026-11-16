# Changing parameters

Each model gets user parameters of its own, numbered per model: the first bin is `gfBin1_…`, the next `gfBin2_…`, the
same for `gfPlate1_…`, `gfLabel1_…` and `gfBox1_…`. Change them in **Modify › Change Parameters** and the model follows without
building it again; changing one model's parameters changes no other.

![Fusion's Parameters window with the user parameters gfBin1_baseWidth, gfBin1_baseLength, gfBin1_heightU and gfBin1_heightUnit of a bin](../assets/images/change-parameters.png)

## Bins

| Parameter | What it holds |
|---|---|
| `gfBin1_baseWidth` | Base width unit |
| `gfBin1_baseLength` | Base length unit |
| `gfBin1_heightUnit` | Height unit |
| `gfBin1_heightU` | Bin height in height units |
| `gfBin1_label` | Label text, with several compartments `gfBin1_label1`, `gfBin1_label2` … for those with a text |

The walls, compartments, label tab, Cullenect pockets, joint origins and raised dividers follow the units. A label
text made longer keeps the height of its letters and can run past the tab: **Gridkeeper rebuild** fits it again. The
size of a Cullenect pocket (1U, 2U …) is chosen when the bin is built; if a change would need another size, rebuild the
bin.

## Baseplates

| Parameter | What it holds |
|---|---|
| `gfPlate1_baseWidth` | Base width unit |
| `gfPlate1_baseLength` | Base length unit |
| `gfPlate1_paddingLeft`, `…Top`, `…Right`, `…Bottom` | Side padding |

The joint origins of the sockets follow the base units.

## Inserts

| Parameter | What it holds |
|---|---|
| `gfLabel1_baseWidth` | Base width unit, only with a width in base units |
| `gfLabel1_width` | Insert width, an expression of the base width, the units and the correction |
| `gfLabel1_text1`, `gfLabel1_text2` | The text lines |

The symbol stays at the right edge when the width changes. A text made longer isn't fitted again, it runs on to the
right; shorten it or rebuild the insert.

!!! tip "Rebuild instead"
    Anything that isn't a parameter, such as the bin size in units or the compartments, is changed with
    [Gridkeeper rebuild](settings-rebuild-clone.md#gridkeeper-rebuild).

## Boxes

| Parameter | What it is |
|---|---|
| `gfBox1_baseWidth` | Width in grid cells of 42 mm, at least 4 |
| `gfBox1_baseLength` | Length in grid cells, at least 3 |
| `gfBox1_heightU` | Height in units of 7 mm, at least 5 |

The cell joint origins of a box keep the cells it was built with, see [Storage boxes](../boxes.md).
