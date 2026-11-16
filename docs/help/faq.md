# Troubleshooting and FAQ

See also [Messages and locked OK](messages.md) for every message Gridkeeper shows.

## Installation

**The commands don't show in Solid › Create.**
Open **Utilities › Add-Ins › Scripts and Add-Ins**, check that Gridkeeper is in the list and running (a green dot or
*Running*). If not, select it and click **Run**. Tick **Run on Startup** so it starts with Fusion. Make sure you picked
the folder that holds the `.manifest` and `.py` files, not a folder above it.

**After an update nothing changed.**
Fusion loads the add-in once, when it starts. Restart Fusion, or **Stop** and **Run** the add-in in **Scripts and
Add-Ins**.

**Can I keep the original GridfinityGenerator?**
Yes, see [Beside the original](../getting-started/installation.md#beside-the-original).

**I installed GridfinityGenerator from the Autodesk App Store, is that Gridkeeper?**
No. The App Store has the original add-in by Le0Michine. Gridkeeper comes only from the
[GitHub releases](https://github.com/Eifel-Joe/FusionGridfinityGenerator/releases).

## Building

**The dialog takes long to react.**
Turn off the preview (**Show auto update preview (slow)**, **Show preview (slow)**); in the bin dialog use **Update
preview once** to look at the result now and then. Large baseplates with joint origins and inserts with many-point
symbols take a few seconds.

**OK is greyed out.**
An input is out of range or a check failed; the dialog says which where it can. See
[Messages and locked OK](messages.md#ok-stays-locked).

**My part design became a hybrid design.**
That's on purpose: every model is a component of its own, a part design can't hold components. See
[Components and joints](../working/components.md#part-designs).

**Fusion shows everything half transparent after building.**
Another component is active. Gridkeeper activates the root after every build; if a build was cancelled in between,
activate the root yourself (double-click it in the browser).

**The Cullenect style is greyed out or gives no pocket.**
Pockets need a label tab, walls of at least 1.2 mm, a hollow or shelled bin and no custom shape. A compartment too
narrow or too short gets no pocket, the Actual dimensions table says so. See [Pockets in bins](../cullenect/pockets.md).

**Label text, icon and color are greyed out.**
The label style is *Cullenect*: the text goes on the insert. Pick another style to get them back; they kept their
values.

**Holes in the base are greyed out.**
The bin is on the **Half grid**: half feet have no room for magnet or screw holes. Or **Generate base** is off.

## Labels and text

**Parts of my letters are missing in the slicer.**
The text is thinner than a 0.4 mm nozzle line. Use a bold or **Heavy** style, a wider tab or insert, or a shorter
text; Gridkeeper warns after building, see [Printable text](../working/colors.md#printable-text).

**I made a label text longer in Change Parameters, now it runs past the tab.**
Letters keep their height when the text changes through its parameter. Right-click the bin › **Gridkeeper
rebuild** › **OK** fits the text again.

**New letters of a longer text have the wrong color.**
Rebuild the bin or insert; the color sits on the Text component and normally carries over.

## Rebuild and settings

**There is no Gridkeeper rebuild in the right-click menu.**
Right-click the **body** of the model (in the canvas, or in the browser under the component › Bodies), not the
component itself. Models built by very old versions without stored settings can't be rebuilt.

**After a rebuild some features are red.**
They used a face or an edge of the old body. The message after the rebuild lists them; edit each and pick its faces
or edges again.

**My insert left its pocket after the bin was rebuilt.**
The pocket of the same name is missing in the new bin, or became too small; the rebuild notes say which. Rebuild the
insert and pick a pocket.

## Printing

**The insert doesn't click in, or falls out.**
Change the fit: **Socket play (mm)** on the bin (larger is looser) or **Correction width** / **Correction height** on
the insert (smaller is looser). Print a test insert first.

**The bins don't sit flat on the baseplate.**
Use the same **Bin xy clearance** on bins and baseplate. **Vertical clearance under bins** lets bins sit on their feet
rather than on the ridges of the plate.

**How do I print the label in a second color?**
See [Colors and multicolor printing](../working/colors.md#bambu-studio).
