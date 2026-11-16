# Compartments and scoop

The **Bin compartments** section of the bin dialog.

## Compartment grid

The small grid at the top sets how many compartments the bin has: **X**, the cells along the bin width, and **Y**,
the cells along the bin length, all the same size.

## Compartment layout

Tick **Edit compartment layout** for a drawing of the grid:

- **Drag across cells** to merge them into a larger pocket. **Split** takes a pocket back to single cells.
- **Click a pocket** to give it its own **Label** text, **Icon** and **Depth**. An empty label takes the text of the
  [label tab section](labels.md); the depth is measured from the top of the bin, empty for the full depth.
  **Done** finishes editing that pocket, changes are applied right away.
- **Reset all** goes back to single cells, without labels or depths.

Unticking **Edit compartment layout** resets the compartments to the uniform grid. Cells under the size the
compartment corners need are reported.

Uniform compartments | Custom compartments A | Custom compartments B
:-------------------------:|:-------------------------:|:-------------------------:
![Uniform compartments options](../assets/ui/bin-uniform-compartments-options.png) | ![Custom compartments A options](../assets/ui/bin-custom-compartments-variant-a-options.png) | ![Custom compartments B options](../assets/ui/bin-custom-compartments-variant-b-options.png)
![Bin with uniform compartments](../assets/models/bin-uniform-compartments.png) | ![Bin with custom compartments A](../assets/models/bin-custom-compartments-variant-a.png) | ![Bin with custom compartments B](../assets/models/bin-custom-compartments-variant-b.png)

<picture><source media="(prefers-color-scheme: dark)" srcset="../../assets/gif/bin-compartments-dark.gif"><img src="../../assets/gif/bin-compartments-light.gif" alt="Merging compartments and naming one, with the bin as compartments are merged and labeled"></picture>

!!! note "Pictures of the original add-in"
    The pictures on this page come from GridfinityGenerator, the layout works the same in Gridkeeper.

## Dividers up to the top on grid lines

**Dividers up to the top on grid lines** (off): compartment dividers lying on a grid line go up to the top of the lip
and run out in its profile. The feet of a bin stacked on top have a groove there, so a bin of any size still stacks
on it. Dividers between grid lines stay below the lip. Hollow bins with a lip and more than one compartment only.

![A 3x2 bin with three compartments, the dividers rising to the top of the lip](../assets/images/bin-dividers-to-top.png)

## Scoop

**Add scoop (along bin width)** adds a rounded scoop along the bin width, so small parts slide out. **Scoop max radius
(mm)** (25 mm) limits its size.

Scoop enabled | Scoop disabled
:-------------------------:|:-------------------------:
![Bin with a scoop](../assets/models/bin-scoop-on.png) | ![Bin without a scoop](../assets/models/bin-scoop-off.png)
