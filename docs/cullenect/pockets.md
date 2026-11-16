# Pockets in bins

In the bin dialog, **Bin compartments › Label tab**: tick **Add label tab (along bin width)** and pick **Label style**
**Cullenect**. Every label tab gets a pocket instead of a printed label, with several compartments every compartment
tab.

![The label tab section of the bin dialog with label style Cullenect: text, icon, bold, color and tab top angle greyed out, Socket play shown](../assets/images/dialog-bin-cullenect.png)

## Pocket size

The pocket takes the widest standard Cullenect width, in half units (1U, 1.5U, 2U …), that fits the tab with 1 mm to
spare at each end. Standard widths keep original Cullenect inserts fitting compartment tabs too. A compartment too
narrow for even a half unit pocket, or too short from front to back for the tab, gets none.

The second row of the **Actual dimensions** table lists each pocket size the bin gets with the insert width that fits
it, for example:

```
Cullenect: 1U: pocket 36.3 mm, insert 36 mm; 2U: pocket 78.3 mm, insert 78 mm
```

The same list, with how many pockets of each size the bin has, is in its **Gridkeeper settings** under *Cullenect*.

<picture><source media="(prefers-color-scheme: dark)" srcset="../../assets/gif/cullenect-pocket-dark.gif"><img src="../../assets/gif/cullenect-pocket-light.gif" alt="A bin with a plain label tab, then the same tab with a Cullenect pocket, then the pocket over 2 units"></picture>

## The tab with a pocket

- The tab is widened to at least 14 mm, more under steep overhangs, and kept flat: **Tab top angle** is switched off.
- **Label text**, **Label icon**, **Bold label text** and **Label color** are switched off too, the text goes on the
  insert. They keep their values for when you switch back to another style.
- A hollow tab keeps a 0.4 mm skin under the pocket.
- **Socket play (mm)** (0.3 mm, like Cullenect, up to 1 mm) is how much larger the pocket is than the insert, in
  width and height. The inserts themselves are made to size; if your inserts sit too tight or too loose, change the
  play here, or the correction of the insert, see [Label inserts](inserts.md#size).

## Requirements

- **Walls of at least 1.2 mm**, the Cullenect standard. Below it **OK** stays locked and the Cullenect row of the
  dimensions table says why.
- Hollow and shelled bins with a body. Solid bins and [custom shapes](../bins/size.md#custom-shape) get no pockets.

## Joint origins

Every pocket gets a joint origin in the middle of its floor, Z up and X along the pocket. Pick it in the
**Pocket** field of the [label dialog](inserts.md#pocket) and the insert is jointed into the pocket, flush and
centered.

## After building

The pockets follow the bin's base unit and height [parameters](../working/parameters.md). Their size (1U, 2U …) is
chosen when the bin is built: if a parameter change would need another size, rebuild the bin from its right-click
menu. A bin rebuilt with inserts in its pockets moves their joints over to the pockets of the same name; a joint whose
pocket the new bin lacks is named in the rebuild notes.
