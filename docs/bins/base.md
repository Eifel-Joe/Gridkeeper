# Base, magnets and screws

The **Base interface features** section of the bin dialog: the feet that sit in the baseplate sockets.

| Input | Default | What it does |
|---|---|---|
| **Generate base** | on | Off builds the body alone, without feet |
| **Add joint origins** | off | A joint origin at the bottom center of every foot, to joint the bin into baseplate sockets or the cells of a storage box ([how](../working/components.md#jointing-by-hand)); only with the base |
| **Add screw holes** | off | A screw hole in every foot |
| **Screw hole diameter** | 3 mm | 1 to 10 mm; with magnet sockets smaller than the magnet cutout |
| **Add magnet sockets** | off | A magnet socket in every foot |
| **Add tabs to magnet sockets** | off | Opens each magnet socket to the side, to pull the magnet out |
| **Magnet cutout diameter** | 6.5 mm | 1 to 10 mm |
| **Magnet size** | 6×2 mm (2.4 mm deep) | Sets the depth for 6 × 2 mm or 6 × 3 mm (3.4 mm) magnets; *Custom* to type the depth |
| **Magnet cutout depth** | 2.4 mm | At least 1 mm, typed with *Custom* |

![The magnet settings of the bin dialog: Magnet size 6×3 mm sets the cutout depth to 3.4 mm](../assets/images/dialog-bin-magnet-size.png)

With magnet sockets and screw holes together, a groove bridges each magnet socket to its screw hole for
printability; it is left out where the sockets are too deep for it. Half size feet have no magnet or screw holes: on the **Half grid** the hole inputs are locked, as they are without
**Generate base**.

Magnet sockets | Magnet sockets opened to the side | Magnets and screws with a groove
:-------------------------:|:-------------------------:|:-------------------------:
![Bin with magnet sockets](../assets/models/bin-magnet-cutouts.png) | ![Bin with magnet sockets opened to the side](../assets/models/bin-magnet-cutouts-with-tabs.png) | ![Bin with magnet sockets and screw holes joined by a groove](../assets/models/bin-magnet-cutouts-and-screw-holes-with-groove.png)

<picture><source media="(prefers-color-scheme: dark)" srcset="../../assets/gif/bin-bottom-options-dark.gif"><img src="../../assets/gif/bin-bottom-options-light.gif" alt="Going through the bottom options in the dialog, with the bin for each"></picture>
