# Saving and loading settings

Every Gridkeeper dialog has a section with buttons for its settings: **Inputs** in the baseplate and label dialogs,
**Changes** in the bin dialog.

![The Changes section of the bin dialog with its buttons for defaults and settings files](../assets/images/dialog-settings-buttons.png)

## Dialog defaults

| Button | What it does |
|---|---|
| **Save as defaults** | The dialog opens with the current inputs from now on |
| **Reset to defaults** | Sets the inputs back to the saved defaults |
| **Clear defaults** | Wipes the saved defaults and sets the inputs back to the original ones |

Without saved defaults a dialog opens with the inputs it had last time in this Fusion session, after a restart with
the original ones. The defaults are stored in the add-in folder
and survive an [update](../getting-started/installation.md#update).

## Settings files

| Button | What it does |
|---|---|
| **Save to file** | Saves the settings to a JSON file |
| **Load from file** | Sets the inputs from a saved file |
| **Copy** | Copies the settings to the clipboard as JSON, e.g. for a bug report |

A file holds every setting by name, lengths in mm and angles in degrees, and which generator it is for:

```json
{
    "generator": "label",
    "generatorVersion": "2.4.0.0",
    "settings": {
        "baseWidth": 42.0,
        "useUnits": true,
        "widthUnits": 1,
        "line1": "M3x10",
        "textStyle": "Heavy",
        "...": "..."
    }
}
```

## Loading older or other files

- A file of another generator, e.g. a baseplate file in the bin dialog, is refused with a message.
- A value of the wrong type refuses the file and says which setting is wrong.
- Settings the file doesn't have, saved by an older version, **keep the dialog's value**, and a message lists them,
  for example a bin file saved before bins had a label color keeps the color chosen in the dialog.
- Settings this version doesn't know are skipped, and a dropdown choice it doesn't offer becomes its default; the
  message lists both.

Files saved by GridfinityGenerator v2.4 load the same way.
