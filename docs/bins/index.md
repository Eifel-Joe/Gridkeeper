# Bins

**Solid › Create › Gridkeeper bin** builds a bin that drops into a baseplate. Every new bin is a component of its
own in the container *Bins*, see [Components and joints](../working/components.md).

![The Gridkeeper bin dialog](../assets/images/dialog-bin.png)

The dialog is long, its sections are described on these pages:

| Section | Page |
|---|---|
| **Info**, **Basic sizes**, **Main dimensions** with the **Actual dimensions** table | [Size and shape](size.md) |
| **Bin features**: body, type, walls, lip, creases | [Body, walls and lip](body.md) |
| **Bin compartments**: layout, dividers, **Scoop** | [Compartments and scoop](compartments.md) |
| **Bin compartments › Label tab** | [Label tab and labels](labels.md), for the Cullenect style also [Pockets in bins](../cullenect/pockets.md) |
| **Base interface features** | [Base, magnets and screws](base.md) |
| **Changes** | [Saving and loading settings](../working/save-load.md) |
| **Preview** | below |

<picture><source media="(prefers-color-scheme: dark)" srcset="../assets/gif/bin-features-dark.gif"><img src="../assets/gif/bin-features-light.gif" alt="Changing the size, type and wall thickness of a bin, with the bin at each change"></picture>

## Preview

Building a bin takes a few seconds, so the preview is off by default.

- **Show auto update preview (slow)** builds the bin again after every change.
- **Update preview once** builds it once with the inputs as they are; it is hidden while the auto update is on.
- **Last preview** shows how long the last preview took and notes text that is too thin to print.

**OK** builds the bin. Some inputs lock **OK** and the dialog says why, for example walls too thin for a Cullenect
pocket or a custom color that isn't `#rrggbb`. If a build fails, for example on a label text that doesn't fit its
label, a panel shows the error with the settings, to copy them into a bug report.
