# Settings, rebuild and clone

Every baseplate, bin, insert and box remembers the settings it was built with. Right-click it, in the canvas or in the
browser, for three commands:

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
- Inserts in the pockets of a rebuilt bin are jointed into the pockets of the same name again.
- A rebuilt box replaces box and lid together, where the old set stood; your joints on its joint origins move over
  to the joint origins of the same name, see [Storage boxes](../boxes.md).
- A rebuilt insert is drawn from the bottom left corner of the old one; if it was in a pocket, the dialog has that
  pocket picked already and the new insert is jointed into it.
- For a bin, changing only what its [parameters](parameters.md) hold, the height and the units, sets the parameters
  instead of building it again. Any change of a label text builds the bin anew, so the text is fitted to its label.

## Gridkeeper clone

Opens the model's dialog with its settings for a **new** model, the original stays as it is. Handy for a second bin
like the first, only higher.
