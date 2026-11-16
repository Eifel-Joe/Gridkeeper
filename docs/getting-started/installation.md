# Installation and updates

Gridkeeper is installed from the ZIP file of a GitHub release. It is **not** in the Autodesk App Store, the
GridfinityGenerator you may find there is the original add-in by Le0Michine.

## Install

1. Download the ZIP file of the latest release from the
   [releases page](https://github.com/Eifel-Joe/FusionGridfinityGenerator/releases).
2. Unpack it to a place that stays where it is, for example `Documents\Fusion add-ins`. The ZIP holds a folder
   `Gridkeeper` with `Gridkeeper.manifest` and `Gridkeeper.py`; keep that folder name, Fusion loads an add-in only
   from a folder named like its manifest. Fusion loads it from there every time it starts.
3. In Fusion open **Utilities › Add-Ins › Scripts and Add-Ins** (or press <kbd>Shift</kbd>+<kbd>S</kbd>).
4. On the **Add-Ins** tab click the **+** next to *My Add-Ins* and pick the `Gridkeeper` folder from step 2.
5. Select Gridkeeper in the list, tick **Run on Startup** and click **Run**.

**Gridkeeper bin**, **Gridkeeper baseplate** and **Gridkeeper label** now show in **Solid › Create** of the Design
workspace.

![Fusion's Scripts and Add-Ins window with Gridkeeper added and Run on Startup ticked](../assets/images/install-scripts-and-addins.png)

## Update

Download the ZIP of the new release and unpack it over the old `Gridkeeper` folder, replacing its files. Restart Fusion, or stop
and run the add-in again in **Scripts and Add-Ins**. Your saved dialog defaults are kept, they are stored in the add-in folder and not part of the ZIP.

## Beside the original

Gridkeeper runs beside the original GridfinityGenerator: its commands have names of their own, so both can be loaded
at the same time. **Solid › Create** then lists *Gridfinity bin* and *Gridfinity baseplate* of the original next to
*Gridkeeper bin*, *Gridkeeper baseplate* and *Gridkeeper label*.

- Models keep working whichever add-in built them; they are ordinary Fusion bodies and components.
- Right-click a model for the commands of each loaded add-in. Use **Gridkeeper settings**, **rebuild** and **clone**
  for models built by Gridkeeper.
- Settings files saved by GridfinityGenerator v2.4 load in Gridkeeper's dialogs; settings Gridkeeper added keep the
  dialog's value, see [Saving and loading settings](../working/save-load.md#loading-older-or-other-files).
- Each add-in keeps its own dialog defaults.

If you don't need the original any more, stop and remove it as below, or uninstall it the way you installed it (the
App Store version through Autodesk's installer).

## Units

The dialogs take any length unit Fusion understands; a number without a unit is in the document's units. All lengths
in this documentation are in millimeters.

## Remove

1. In **Scripts and Add-Ins** select Gridkeeper and click **Stop**; untick **Run on Startup**.
2. Remove it from the list with the menu of its row.
3. Delete its folder. This also deletes your saved dialog defaults.

Models built with Gridkeeper stay as they are, with their user parameters; only the right-click commands to show,
rebuild or clone them are gone until you install it again.
