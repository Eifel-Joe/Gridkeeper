# Installation and updates

Gridkeeper is installed from the ZIP file of a GitHub release. It is **not** in the Autodesk App Store, the
GridfinityGenerator you may find there is the original add-in by Le0Michine.

## Install

1. Download the ZIP file of the latest release from the
   [releases page](https://github.com/Eifel-Joe/FusionGridfinityGenerator/releases).
2. Unpack it into a folder of its own that stays where it is, for example `Documents\Fusion add-ins\Gridkeeper`.
   Fusion loads the add-in from this folder every time it starts.
3. In Fusion open **Utilities › Add-Ins › Scripts and Add-Ins** (or press <kbd>Shift</kbd>+<kbd>S</kbd>).
4. On the **Add-Ins** tab click the **+** next to *My Add-Ins* and pick the folder from step 2, the one holding
   the `.manifest` and `.py` files.
5. Select Gridkeeper in the list, tick **Run on Startup** and click **Run**.

**Gridkeeper bin**, **Gridkeeper baseplate** and **Gridkeeper label** now show in **Solid › Create** of the Design
workspace.

![Fusion's Scripts and Add-Ins window with Gridkeeper added and Run on Startup ticked](../assets/images/install-scripts-and-addins.png)

## Update

Download the ZIP of the new release and unpack it over the old folder, replacing its files. Restart Fusion, or stop
and run the add-in again in **Scripts and Add-Ins**. Your saved dialog defaults are kept, they are stored in the add-in folder and not part of the ZIP.

## Beside the original

Gridkeeper runs beside the original GridfinityGenerator: its commands have names of their own, so both can be loaded
at the same time.

## Units

The dialogs take any length unit Fusion understands; a number without a unit is in the document's units. All lengths
in this documentation are in millimeters.

## Remove

In **Scripts and Add-Ins** select Gridkeeper, click **Stop** and remove it with the menu of its row, then delete its
folder. Models built with it stay as they are.
