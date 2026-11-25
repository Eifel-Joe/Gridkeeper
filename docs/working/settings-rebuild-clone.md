# Settings, rebuild and clone

Every baseplate, bin, insert, box and box label remembers the settings it was built with. Right-click it, in the
canvas or in the browser, for three commands:

<picture><source media="(prefers-color-scheme: dark)" srcset="../../assets/images/context-menu-dark.png"><img src="../../assets/images/context-menu-light.png" alt="Fusion's right-click menu on a face of a bin, with Gridkeeper settings, Gridkeeper rebuild and Gridkeeper clone at its end"></picture>

A letter of a label or a face of the model works as well as the body: Gridkeeper finds the bin or insert it belongs
to. In the browser, right-click the **body**, not the component.

## Gridkeeper settings

Opens a window with the version that built the model and everything it was built with, grouped like its dialog, and the user parameters that drive
it with their current values. For a bin with Cullenect pockets it lists the built tab width and each pocket size with
how many pockets of it the bin has.

![The Gridkeeper settings window of a bin: the buttons, the version it was built with, its parameters and settings](../assets/images/settings-window.png)

Its buttons:

| Button | What it does |
|---|---|
| **Save to file** | Saves the settings to a JSON file, see [Saving and loading settings](save-load.md) |
| **Copy** | Copies them to the clipboard as JSON |
| **Clone into new bin** (baseplate, label) | The same as **Gridkeeper clone** |
| **Rebuild** | The same as **Gridkeeper rebuild** |

Models built by older versions without stored settings show what they have, without buttons; they can't be rebuilt
or cloned.

## Gridkeeper rebuild

Opens the model's dialog with its settings. Change what you like and click **OK**: the model is built again **in its
place in the timeline**, and the features after it keep working on the new body. The Info section of the dialog says
which model is rebuilt.

- Features that used a face or an edge of the old body may need them picked again; Gridkeeper lists them in a message
  after the rebuild.
- A bin or baseplate stays in the component it was in.
- Inserts in the pockets of a rebuilt bin are jointed into the pockets of the same name again. A bin the bin dialog
  put into a cell goes into that cell again.
- A rebuilt baseplate moves joints on its socket joint origins over to those of the same name, bins jointed into it
  stay in.
- A rebuilt box replaces box and lid together, where the old set stood; your joints on its joint origins move over
  to the joint origins of the same name, see [Storage boxes](../boxes.md).
- A rebuilt insert is drawn from the bottom left corner of the old one; if it was in a pocket, the dialog has that
  pocket picked already and the new insert is jointed into it.
- A rebuilt box label goes into the holder of its box again, the dialog has the box picked already; a label without
  a box stays where it was, see [Storage boxes](../boxes.md#label).
- A bin is always built anew, also when you changed only what its [parameters](parameters.md) hold, the height and the
  units (since 1.4.0); its label text is fitted to its label again. To change those values without building the bin
  again, change its parameters in **Modify › Change Parameters**.
- Names you gave the model's component, its timeline group or its bodies stay; a name Gridkeeper gave follows the new
  size. A box part you renamed, its lid or a latch, keeps its name too.
- The component that was active before is active again afterwards.

## Gridkeeper clone

Opens the model's dialog with its settings for a **new** model, the original stays as it is. Handy for a second bin
like the first, only higher. A cloned insert or box label has no pocket or box picked; pick one for the new one.
