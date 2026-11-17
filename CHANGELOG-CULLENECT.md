# Changelog — Cullenect labels

Changes of Gridkeeper (`Eifel-Joe/Gridkeeper`, until 16.11.2026 `Eifel-Joe/FusionGridfinityGenerator`) on top of
GridfinityGenerator by Le0Michine, merged up to 5627083 (17.11.2026; rounds 1 to 11 were built on v2.2.0.0, round 22 merged v2.4.2.0).
Gridkeeper counts its own versions from 1.0.0; its tags are `gridkeeper-vX.Y.Z`, the `vX.Y.Z.W` tags belong to GridfinityGenerator.

## 1.1.0 (2026-11-17)

### Export in print orientation (round r29-export)

- **Parts in print orientation:** the 3MF lays every part the way it is printed instead of where it is in the design
  (Jörg: „Noch in 1.1.0, mit Druckbett-Auswahl. Auch für die 3MF bei Bins und Baseplates wichtig. Ebenso Labels.“):
  the box set's handle flat, its latches flat, the Pinned hinge's pin on its flat side, Cullenect inserts on their
  underside and Flush ones on their text; bins, baseplates, box, lid and hinges as designed. The box parts follow
  [Pred's storage box](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric)
  (CC BY-NC, by Pred). STL files come in print orientation too, STEP stays as designed.
- **Print bed, spacing, purge tower:** the export dialog picks the bed (the baseplate dialog's printers or a size of
  its own), the spacing between the parts (5 mm) and, with colored label text, a square kept free for the purge tower
  (50 mm). The parts are spread over the bed, what doesn't fit goes on further plates, a 3MF file per plate
  (Jörg: „Eine Sortierung kann ja nur bei eine 3MF je Platte anständig durchgeführt werden.“), so the slicer keeps
  its printer, filament and process settings. The choices are kept.
- **Bambu Lab printers apart (click test):** the printer list of the export and baseplate dialogs has every Bambu
  Lab printer of Bambu Studio's profiles, the old *Bambu Lab A1, P1, X1* entry is split (a baseplate saved with it
  opens as *Custom* 256 × 256). The export keeps the purge tower's square where Bambu Studio puts the tower and,
  for the P1 and X1, keeps clear of their excluded corner, which made Bambu Studio warn of collisions.
- **Parts as a compact group:** the parts of a plate lie as a roughly square group in the middle of the bed, not in
  a row across its whole width (Jörg: „Was mir nicht gefällt ist, dass die Kleinteile über die volle Breite angelegt
  sind. Diese könnten kompakter verteilt sein.“).
- **A box set on three plates:** box, lid and small parts each on plates of their own (Jörg: „Das Zubehör der Box
  sollte auf eine separate Platte. Eine Box müsste je nach Größe 3 Platten gesamt ergeben.“).
- **Pinned hinge's halves named after it:** *BottomHingePart_Pinned*, *TopHingePart_Pinned* (Pred names them like the
  M3x30 hinge's).
- **Box label is a part of the export (p380):** All Gridkeeper parts takes the box label with its text, a Flush label
  lies on its text.

### Joint origins explained

- [Joint origins](docs/working/components.md#joint-origins) is now a guide (Jörg: „Wir müssen auf jeden Fall noch
  anständig erklären, wie die Joints generell genutzt werden …“): which joint origins every model has, how to pick one
  in the insert and box label dialogs, how to joint a bin into a baseplate or box cell and a box onto a box by hand,
  and what to do when a joint origin can't be seen or picked.

### Small parts drawn in code (round 29)

- **Box from the dialog with its small parts:** with the parts imported from files (round 28) the box command failed at the first small part
  and was taken back: Fusion can't import a part file in a command that shows a dialog
  (`fusion-auftraege/r28_cmdvariants.log`). Latches, handle, handle pins and the three hinges are now drawn in code,
  each in Pred's shape to the micrometre (compared with Pred's parts, nothing left over), every sketch fully
  constrained, inside the box command and so in the box's timeline group; rebuild and clone alike. The part files of
  round 28 are gone.
- **Small parts in a colour of their own:** *Gridkeeper box parts*, orange like Pred's latch; box and lid stay as they
  are (Jörg: „Im Übrigen brauchen Latches, Hinge, Handle und Pin eine andere Farbe als die Box und der Deckel.“).

### Box label (round 29)

- **Gridkeeper box label (p262):** a new command makes the label for the holder of a box after
  [Pred's storage box](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric) (CC BY-NC):
  Pred's flat plate sized after the box's width, a large text at the left, two lines and up to five
  [Cullenect](https://github.com/CullenJWebb/Cullenect-Labels) symbols (MIT, CullenJWebb) at the right, raised, set in
  or flush like the Cullenect inserts. Picking the *Label joint origin* of a box joints the label into its holder; every
  box now has that joint origin. A command of its own, so a label can be swapped without touching the box. Every
  sketch is fully constrained.
- **Settings, rebuild and clone for the box label:** Jörg after his test: „Die Box-Labels haben die Punkte
  [Gridkeeper settings / rebuild / clone im Rechtsklick] nicht. Warum? Die Cullenect-Label haben es.“ Now they do,
  like the Cullenect inserts: the label keeps its settings, a rebuild builds it anew in place and jointed into the
  holder of its box again, a clone opens the dialog with its settings and no box.
- **The holder stays shown:** Fusion turns off a joint origin a joint uses and leaves it off when the joint goes; after
  a rebuild without its box the box's *Label joint origin* was hidden. Jörg: „Allerdings darf er nicht ausgeblendet
  werden.“ The box label and the Cullenect insert now keep the holder or pocket they are jointed into shown, and a
  rebuild shows the one the old label or insert leaves.

### Small parts of the storage box (round 28)

- **Latches, handle, pins and hinges (p261):** every box set now holds Pred's small parts, taken over from
  [Pred's file](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric) (CC BY-NC),
  drawn in code since round 29: four latches (two at the front, one on each side at the back), the handle and
  its two pins, rigidly jointed at joint origins of the box, and two hinges jointed beside the box in their print
  position. The handle follows the label width (+28.5 mm, at most 113.5 mm). **Hinge** picks one of Pred's three
  hinges (M3x30, the default; Pinned; Plain); settings saved before load with M3x30. Every sketch of the parts is fully constrained,
  none uses a user parameter.
- **Right-click on the set (click test F1):** the set's component offers settings, rebuild and clone like box and lid.
- **Export file names (click test F3):** box bodies carry the set's name, e.g. *Box 5×4×6 Base*.
- **No files in the add-in folder (p292):** importing the part files wrote a folder `_XRef_` beside them; with the parts
  drawn in code (round 29) nothing is imported any more.

### Storage box after Pred (round 27)

- **Gridkeeper box (p260):** a new command builds a storage box with lid after
  [Pred's parametric Gridfinity Storage Box v1.1](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric)
  (CC BY-NC), measure for measure: outer size, grooves, latch catches and slides, hinge slots, handle and label
  holders, lid pins and stacking rim, checked step by step against Pred's file (5 × 4 × 6: the lid's volume is the
  same, the box's differs by Pred's 0.0001 mm deep "switched off" magnet holes). Width and length from 4 × 3 cells,
  height from 6 units for now (Pred goes down to 5, p264), in the parameters `gfBox1_baseWidth`, `gfBox1_baseLength`, `gfBox1_heightU`. Every sketch is
  fully constrained. The set is a component in the container *Boxes* with the components *Box* and *Lid*, the lid
  jointed shut; joint origins in every cell, for stacking and for the lid. Settings, rebuild and clone as for bins.
  Changes to Pred's box: magnet holes of a size of your choice, the floor pads and the stacking rim drawn from circles
  instead of arcs. Height 5 is left for later (p264).
  Latches, hinges and handle followed in round 28, the label in round 29.
- **Magnet size (p263):** bins, baseplates and boxes have a choice before the magnet cutout depth: 6 × 2 mm magnets
  (2.4 mm deep), 6 × 3 mm magnets (3.4 mm, not for boxes: it would break through the floor) or *Custom*. Only the
  depth is saved, older settings files load unchanged.

### Update check (p310)

- **Gridkeeper looks for new versions itself:** once a day at startup, in the background, it asks GitHub's API for
  the newest `gridkeeper-vX.Y.Z` release (GridfinityGenerator's `vX.Y.Z.W` tags never count, nor drafts and
  pre-releases). A newer one opens **Gridkeeper updates** with the version, the first paragraph of its release text
  and a link to the release notes.
- **Update now** downloads the release ZIP, checks it against GitHub's SHA-256, its manifest version and its paths,
  unpacks it next to the add-in and only then swaps the folders, with the old one as backup and put back on any
  failure (if Windows won't move the folder, the new version is copied over it after a full backup). Saved dialog
  defaults, the update setting and added symbols are carried over. The new version loads after a restart of Fusion
  or Stop and Run in Scripts and Add-Ins, both measured in Fusion with every command working; reloading the add-in's
  modules in place left the commands dead and isn't offered.
- A git checkout is never replaced, there the window only points to the release notes.
- **Utilities › Add-Ins › Gridkeeper updates** shows the version running and the one installed, checks right away
  and turns the check at startup off. No network, no message: errors are only logged. The request sends nothing
  but the user agent `Gridkeeper-update-check`.

### Merged from upstream: export (17.11.2026)

Commits of FusionGridfinityGenerator by Lev Mishin (Le0Michine, CC BY-NC-SA 4.0), `513e6ab..5627083`, merged with his
authorship kept:
- **Export from the right-click menu** (4b2f167, `lib/stlFile.py`): one 3MF of all selected parts or an STL or STEP file
  each, the right-click entry below *Save As Mesh*, here called **Gridkeeper export**.
- **3MF with painted label letters** (e4c885f, `lib/threeMf.py`): the letters get a filament index Bambu Studio,
  OrcaSlicer and PrusaSlicer pick up without painting by hand.
- **Colored outline letters in Fusion** (d0ad89c, `lib/labelFaces.py`): the letters of an outline label get an
  appearance of their own. In this fork only for labels without a color; a colored label has letter bodies of its own.
- **Exact bin size in the dialog** (a8233fb): the actual dimensions follow the xy clearance and the lip to the micron.
- **Plate edge clearance per edge** (3452e56): *Clearance between plates* becomes *Plate edge clearance* (half the old
  gap), *Extra bottom thickness* *Bottom padding*, *Vertical clearance under bins* *Top trim*. Settings saved before
  are read under the new name, in this fork on every way settings are read (load, rebuild, clone). The settings of five
  baseplate shape tests carry the new name, their shapes are the same.
- **Developer tools** (873db19, b287cf3, 45d280a, 568f7af, 2588dd7): model pictures that show what a setting changes,
  the export dialog in the dialog screenshots, new picture presets; the release workflow on the Node 24 actions. Their
  output stays in `tools/screenshots/out/`.
- In this fork (p300): the export takes every part, bins, baseplates, Cullenect inserts and, once merged, the boxes
  of round 27 (`lib/exportParts.py`, one list to add new parts to). The colored text and symbol bodies of bins and
  inserts go into the 3MF object, the STL and the STEP file of their part, painted with the label filament in the
  3MF. A letter in the right-click menu stands for its part.
- Not taken over: the wiki with its workflow and generator, the contribution guide, the README text and every
  picture and diagram (the documentation keeps its own), the version bump.

### Merged from upstream (17.11.2026)

Thirteen commits of FusionGridfinityGenerator by Lev Mishin (Le0Michine, CC BY-NC-SA 4.0), `fba170e..513e6ab`, merged
with his authorship kept:
- **Lip type** *Light* (default, as before) or *Full*, the original Gridfinity profile with an inner tip and a support
  under it, and **Trim lip top** (on by default, as before; off keeps the sharp top edge), each with its profile
  beside it in the dialog. Seven new shape tests.
- **Context menu on bin and baseplate components:** settings, rebuild and clone also when the component of a bin is
  selected rather than its body, beside this fork's own handling of bodies and label letters.
- **Developer tools:** the test window filters cases by status and updates a snapshot right away; the model pictures
  palette searches by name, cuts pictures through their middle and takes the dialog screenshots. Their output stays
  in `tools/screenshots/out/`.
- In this fork: dividers raised up to the top under a full lip get the narrowing foot bottom of the lip socket around
  them, a new shape test for it.
- Not taken over: the README text and every picture and animation (the documentation keeps its own pictures), the
  version bump (Gridkeeper keeps its own version).

## 1.0.0 (2026-11-16)

### Gridkeeper (rounds 23 to 25)

- **New name Gridkeeper:** the add-in, its commands, the menu entries and the manifest (`Gridkeeper.manifest`,
  `Gridkeeper.py`, a new id, version 1.0.0). Settings saved in designs keep their `gfBin`/`gfPlate`/`gfLabel`
  parameter names and their attribute group, so designs made with GridfinityGenerator or earlier versions of this
  fork are still recognised by settings, rebuild and clone.
- **New README** and a full **documentation site** in English (`docs/`, MkDocs Material, published on
  https://eifel-joe.github.io/Gridkeeper/): installation from the release ZIP (not the Autodesk App Store), every
  dialog and option, Cullenect pockets, inserts and symbols, settings files, the snapshot tests, deviations from the
  Gridfinity spec (the lip, GridfinityGenerator issue #176), credits.

### Own pictures and animations (round 26)

- Every picture and animation of the documentation is Gridkeeper's own now. The 25 animations and 55 pictures taken
  over from GridfinityGenerator are replaced or, where no page used them, removed.
- 15 animations in the layout of the original (model, dialog part, caption), built from Fusion renders and dialog
  screenshots by `dev-notes/tools/anim/compose.py`; new ones for Cullenect pockets, insert text and symbols, and a
  solid bin with a tool cut in place of the nozzle screen recording.
- Seven pictures (five dialogs, the settings window, the test report) retaken without the reddish edge the
  screen-control glow left on them. `tools/screenshots` and "Gridkeeper docs: render models" now write to
  `tools/screenshots/out/` so they cannot overwrite the documentation pictures.

### Merged from upstream (round 22)

Six commits of FusionGridfinityGenerator by Le0Michine (CC BY-NC-SA 4.0) merged as they are, his authorship kept:
- **"Gridfinity clone" in the context menu**, beside the Clone button of the settings window. With this fork it clones
  inserts too.
- **More label icons:** button head and countersunk screws (Phillips, slotted, self-tapping, Phillips self-tapping), a
  grub screw and a hex locknut.
- **Label icon keeps its full size** (Joerg: "as the original"): only the text shrinks to the width left after the
  icon, the letters stand on the icon's bottom. Rebuilt in this fork's label code, the least text height of round 19
  still applies.
- Not taken over, decided in this fork: the version bumps (the version stayed 2.4.0.0 until the rename to Gridkeeper 1.0.0); rebuilding with a new label
  text, which this fork does since round 19 for compartment labels too.

### Thin text hint and room on inserts (round 21)

- **Hint at the print limit (p232):** the hint on text too thin to print follows the measured least height of each
  style (Regular 4.43 mm, Bold 3.42 mm, Heavy 3.05 mm, round 17), the same number the fitting stops at, instead of an
  estimated mean stroke under 0.6 mm. Heavy is hinted from 3.05 mm instead of 2.79 mm, Regular and Bold a little later
  than before. On a bin the hint now says to make the tab wider (or use Bold), a text too wide isn't built anyway.
- **Room without a symbol (p233):** an insert's text is fitted with 1 mm room at the right edge also without a symbol,
  as before a symbol (round 17), so an insert made up to 1 mm narrower afterwards keeps the text inside.

### Bin label text made longer (round 19)

- **Rebuild fits a longer text again (p181):** a bin label text made longer through its parameter keeps the height of
  its letters and can run past the tab. "Gridfinity rebuild" now builds such a bin anew and fits the text to its
  label, also when only the parameter was changed; before, it just set the parameter again. Fusion can't make a
  sketch text's height follow the length of its text by parameters (tried 16.11.2026), so the fit happens on rebuild.
- **Least text height on bin labels:** a text shrinks for the width of its label only down to the height where the
  thinnest stroke is one 0.4 mm nozzle line (Regular 4.43 mm, Bold 3.42 mm, round 17). A text that doesn't fit even
  then isn't built, the dialog says which text; a tab lower than that keeps its own height.
- **Umlauts on two-line inserts (p210):** measured, the dots of Ä, Ö and Ü stay inside the insert in every style, also
  with -1 mm height correction; nothing to change.

### Rebuilding inserts and their settings (round 18)

- **Inserts like bins (p150):** an insert of the Gridfinity label command can be rebuilt in its place from the context
  menu, "Gridfinity rebuild", and its settings saved to a file, loaded, copied and cloned from "Gridfinity settings", as
  bins and baseplates since upstream v2.4. This reuses the rebuild and config mechanism of FusionGridfinityGenerator
  by Le0Michine (CC BY-NC-SA 4.0). A rebuilt insert is drawn from the bottom left corner of the old one and keeps its
  parameters; an insert jointed into a Cullenect pocket gets a new joint into the same pocket. Inserts built before
  this version have no config in their tag and can't be rebuilt, their settings still show.
- **Old bin configs keep the label color (p151):** loading a bin config saved before bins had a label color keeps the
  color chosen in the dialog instead of setting it to None.

### Insert geometry (round 17)

- **Descenders stay on the insert (p110):** two lines on an insert made lower by its height correction shrink so that
  g, j, p and y end above the bottom edge. They never shrink below the least height of their style, where the
  thinnest stroke of the font is one line of a 0.4 mm nozzle (Regular 4.43 mm, Bold 3.42 mm, Heavy 3.05 mm, measured
  on the letters in Fusion, `tools/fontStroke.py`). Where that isn't enough the dialog says so and won't build: two
  lines in Regular from about -0.45 mm correction, in Bold from about -0.57 mm.
- **Debossed rim stays whole (p140):** set in, the symbol keeps 0.4 mm off the edges, so the top layer over the latch
  isn't cut through and the insert still holds. Flush and embossed are as before.
- **Room before the symbol (p52):** a text is fitted with 1 mm more room before the symbol, so an insert made up to
  1 mm narrower afterwards doesn't push the symbol onto the text.
- **Faster hardware symbols (p51):** the hardware symbols are rendered with coarser circles, about a tenth of the
  points, the contour within 0.05 mm. An insert with a nylon lock nut builds in about 3 s instead of 24 s, with a closed
  crimp ring in about 4 s instead of 33 s. The symbols are still derived from Cullenect-Labels by CullenJWebb (MIT).
- **Symbols on bin labels (p180):** measured again on the coarser symbols, the limit of symbols held by dims on a bin
  label stays at 40 points: up to the hex nut (36 points) that takes under 2 s, from the magnet (50 points) on 3 s and
  more, those are still moved into place.

### Tests and the settings window (round 16)

- **Shape tests green on any font (p30):** bins with a text label are compared by their form, the number of bodies,
  their volume and the box around them, not by where each letter lies, which depends on the font and the Fusion
  version. A setting newer than a snapshot counts as a change only when the case has it off its default. The whole
  run is green again, 83 of 83, without recording those snapshots anew.
- **Previews in any language (p31):** the color of the snapshot previews and model pictures is found through the
  appearance library's id, as for the label colors, so a Fusion with a German library takes previews too; without
  any, the picture is taken in Fusion's own look.
- **Checks in the test run (p34):** a check after a build that breaks shows as a check failure, not as a build failure,
  and the build with a case's parameters from the start gets its sketches checked as well.
- **Gridfinity settings of a Cullenect bin (p32, p33):** the Cullenect section shows the label tab width as built,
  widened for the socket, and a row per socket size with how many sockets of it the bin has, e.g. "1U: 8 sockets".
  Bins built before keep the list they were built with.

### Grid and bin geometry (round 15)

- **Joint origins follow the grid (p170):** the joint origins of bin feet and baseplate sockets sat in one sketch on
  reference dimensions and stayed put when a base unit changed. Each is now a point of its own with driving
  dimensions, so after changing `gfBinN_baseWidth` or a baseplate's base width they stay in the middle of their cells.
  A 6x6 baseplate with joint origins builds in about 9.7 s instead of 7.0 s.
- **Labels and sockets beside the grid (p60):** where a tab and its compartment overlap is now worked out by Fusion
  (`max()`/`min()`), not picked once when building, for Cullenect sockets, text labels, the tab hollow and its
  openings. The size of a Cullenect socket (1U, 2U …) is still chosen when building: if a parameter change would need
  another size, rebuild the bin from its context menu.
- **Raised divider corners on thick walls (p101):** a wall thicker than the lip leaves a small ledge under the lip.
  The corners of dividers up to the top are now rounded in one go on both sides of it, at 2 and 3 mm walls, instead of
  falling back to a smaller rounding with a step.
- **Cullenect needs 1.2 mm walls (p35):** the Cullenect label style needs a wall of at least 1.2 mm, the Cullenect
  standard (Joerg: thicker is fine, thinner not). Below it the bin dialog keeps OK locked and says why in the
  Cullenect row of the dimensions table, also when a config is loaded or a bin is rebuilt. Bins built before stay.

### Labels after a text change (round 14)

- **Bin labels stay put (p72):** a label text made longer through its parameter added letters at the origin, untilted
  and outside the bin, because the label was laid out at the current spot and moved there body by body. The text of a
  bin and compartment label is now drawn where it ends up: on planes that follow the bin's parameters, a tilted tab
  through three points, standing on a baseline whose ends follow the label's width. The cut into the bin (engraved,
  outline) or the join (embossed) is the extrusion's own operation, so new letters are cut or joined too. Small icons
  (up to 40 points, e.g. the hex nut and screws) are held there by dimensions; the large Cullenect symbols are still
  moved into place, as their bodies never change with the text (p180). Bins built before stay as they are until they
  are rebuilt from their context menu.
- **New letters show the color (p120):** the label color goes on the Text component of a bin or insert instead of on
  each body, so letters a longer text adds show it, also in the 3MF export.
- **Context menu on a new letter (p71):** "Gridfinity settings" and "Gridfinity rebuild" now find the bin or insert
  from a letter in its Text component that has no tag of its own. New letters keep Fusion's body names.
- Found in this round: a 3MF export lists every letter as an object of its own, not the Text component as one part
  (p53 stays open); a label text that already fills its label runs past it when made longer (p181).

### An assembly of components, inserts jointed into their pockets (round 13)

- **Containers Grid, Bins and Label:** every new baseplate, bin and Cullenect insert is a component of its own in the
  container of its kind, directly in the root. A part design is switched to hybrid for it, as it was for inserts
  before; a preview leaves it a part. The containers are found by a tag, so they may be renamed. They are grounded, so
  a joint of a part in them moves that part only, not the container with everything in it.
- **Text components:** the colored text and symbol bodies of a bin or an insert are in a component Text inside it, so
  they export apart for a multicolor print. They are built there, so letters a longer live text adds land there too.
  Engraved or uncolored labels have no bodies of their own and get no Text component.
- **Rebuild keeps the place:** a bin or baseplate rebuilt from its context menu stays in the component it was in. Parts
  built before this round stay where they are: bodies in the root of a part design are rebuilt as bodies in the root.
- **Joint origins on the pockets:** every Cullenect pocket gets a joint origin mid floor, Z up and X along the pocket,
  whatever "Add joint origins" says. It follows the bin's base units and height. Every insert gets one mid bottom.
- **Pocket in the label dialog:** pick the joint origin of a pocket, and the insert is jointed into it, flush and
  centered. An insert wider or higher than that pocket isn't built; the dialog asks for a pocket that fits.
  Without a pocket the insert goes beside every bin, baseplate and insert, no longer into the first bin at the
  origin.
- **Rebuild keeps the inserts:** a bin rebuilt with inserts jointed into its pockets moves the joints over to the
  pockets of the same name of the new bin. A joint whose pocket the new bin lacks is named in the rebuild notes.
- Known limit, found in this round (p170): the joint origins of the feet and baseplate sockets from upstream v2.4 sit
  on reference dimensions and don't follow a changed base unit. The pocket ones are driven.

### Base raised to upstream v2.4.0.0

The fork now builds on GridfinityGenerator v2.4.0.0 by Le0Michine (CC BY-NC-SA 4.0), merged with its history, so every
upstream commit keeps its author: bins and baseplates rebuilt in place from their context menu with parameters of
their own, configs saved, loaded, copied and cloned, a panel for build errors, lip notches made from one notch along
the walls, shelled bins with rounded offsets, a clearance between baseplates glued side by side.

- **The inputs of this fork go along:** dividers up to the top, label color and socket play are kept in a bin's
  config, so a rebuild, a clone or a loaded config brings them back into the dialog, the color into its dropdown or
  custom text. Configs saved without them keep the dialog's values.
- **Units of their own:** a bin's Cullenect sockets and raised dividers follow the bin's own `gfBinN_baseWidth`,
  `gfBinN_baseLength` and `gfBinN_heightUnit` instead of the shared `gfBaseWidth`, `gfBaseLength` and `gfHeightUnit`
  that upstream dropped. Every insert of the label command gets its own `gfLabelN_baseWidth` the same way.
- A rebuild that only changes the text of a **colored** bin label builds the bin again instead of setting the text
  parameter, so new letters get the label color too.
- A rebuild pairs the bin bodies only, not the colored label bodies beside them, with the old ones, so the features
  after the bin keep using it.
- A rebuild of a bin with Cullenect sockets that changes its base units builds it again, so the number of socket
  units and the sockets of short compartments are worked out anew; setting `gfBinN_baseWidth` by hand still keeps
  them. Rebuilding a bin without a label to color leaves the dialog's color choice as it was.
- The root component stays active (see below) also after a bin or baseplate is rebuilt in place from its context
  menu, the rebuild builds through the same builder.
- Known limit: colored label bodies have no tag of their own, a feature after the bin that uses one of them has to
  pick it again after a rebuild (Fusion reports it).
- The rounded corners of raised dividers reach the top again on v2.4.0.0's lower lip socket: its inner face ends in an
  edge rising only 3.55 um, which the corner took for level, and stopped short of the top in ledges of 1.40 mm2.
- Raised dividers follow the lower lip socket of v2.4.0.0: the feet of a stacked bin are cut out of them as low as
  out of the lip, so the ridge between two feet stays as high as the lip around it.
- Shape test cases list only the settings that differ from the defaults, like upstream's; inserts have defaults of
  their own (`lib/defaultSettings.py`, `LABEL`). The text style of an insert (Heavy by default, round 11) is one of its
  settings there; bin labels keep their bold switch, which the label generator turns into Regular or Bold.
  A rebuild that only sets a bin label's text parameter gives no thin-text hint, it builds no label; a failed build
  gives none either.

### Added

- **Label style „Cullenect“ for bins.** Every label tab, also each compartment tab and the tab of a shelled bin,
  gets a socket for exchangeable Cullenect label inserts instead of a printed label: 1.2 mm deep, 0.3 mm larger than
  the insert, with the latch ribs along both long sides. The socket takes the widest standard Cullenect width
  (`42 mm × n − 6 mm`, in half units) that fits the tab with 1 mm to spare, so original Cullenect inserts fit compartment
  tabs too. Its width is an expression on the bin's base width parameter and it follows parameter changes like the labels do.
- The tab is widened to at least 14 mm (more under steep overhangs) and kept flat with this style; text, icon, bold and
  tab top angle are switched off in the dialog but keep their values. Hollow tabs keep a 0.4 mm skin under the socket.
- **Socket play** input in the label tab section (default 0.3 mm like Cullenect, 0–1 mm).
- **Socket widths in the dialog:** a second row of the dimensions table lists each socket size of the bin with the
  insert width that fits it, and the bin's „Gridfinity settings“ keep the same list under „Cullenect“.
- **Sketch constraint check** in the shape tests: Cullenect cases fail on a sketch that is not fully constrained,
  other cases log such sketches. Eleven new Cullenect bin cases.
- **Cullenect symbols as svg files:** 480 screw combinations (head, shaft, threads, driver, flange,
  security pin) and 18 hardware symbols in `lib/gridfinityUtils/cullenectIcons/`, rendered once from
  Cullenect's own OpenSCAD code by `tools/cullenectIcons.py`. The add-in reads the folders, so a new symbol is a new
  svg file.
- Symbol catalog `lib/gridfinityUtils/cullenectCatalog.py` (building blocks, file names, lookup from
  the folders, svg size).
- The hardware symbols are also in the label icon dropdown (`Cullenect washer`, ...), with the new
  icon types inserts, magnets and crimps.
- **Command „Gridfinity label“** in the Create menu beside bin and baseplate: a Cullenect insert (`42 mm × n − 6 mm` ×
  11 mm × 1.2 mm with the latch set in 0.2 mm all around, as `cullenect_base_v2`) with up to two lines of text and a
  screw put together from head, shaft, threads, driver, flange and security pin, or a hardware symbol. Width in base
  units (following the insert's own `gfLabelN_baseWidth`) or free in mm, a width and height correction like Cullenect's `offset_xy`. Text and
  symbol are two layers (0.4 mm, see p130 below), raised, set in or flush, and bodies of their own to print them in another colour.
  The width is a user parameter (`gfLabel1_width`), the symbol stays at the right edge when it changes. Each text line
  is a user parameter too (`gfLabel1_text1`, `gfLabel1_text2`) and stays live text, so it can be changed later like
  the bin labels; the font size is fitted when the insert is generated, a longer text stays on one line. All other
  sketches are fully constrained.
  Settings can be saved as defaults and shown with „Gridfinity settings“. Four label shape test cases.
- **Dividers up to the top on grid lines** (bin dialog, off by default): compartment dividers lying on a grid line go
  up to the top of the stacking lip. The feet of a bin stacked on top have a groove on every grid line, so a bin of any
  size still stacks on it, like a 4x2 on two 2x2. The dividers are cut by the feet of a stacked bin with clearance, so
  a divider a little off its line (dividers over many units are) or a thick one only keeps what fits. Dividers between
  grid lines (3 compartments on 4 units, half cells) stay below the lip. Hollow bins with a lip only; follows parameter
  changes. Two new bin cases.

- **Set screws as screw symbols:** head „None“ with a slot, hex or torx driver is a set screw (grub screw): the thread
  as Cullenect draws it and, a gap beside it, its end with the driver, with or without a security pin (hex, torx),
  shaft „Machine“ with a flat end, „Tapping“ with a point. Ten svgs in `cullenectIcons/setscrews/`, rendered by
  `tools/setScrewIcons.py` from `tools/setscrew/SetScrew.scad`. Own work of this fork under MIT, not Cullenect code;
  it uses Cullenect's thread and driver shapes. 15.56 mm wide, 1 mm wider than the other screws. New label case.
- **Text color (inserts and bin labels):** „Text color“ in the label dialog and „Label color“ in the bin dialog,
  None (as before), eight named colors or a custom `#rrggbb`. The text and symbol bodies of an insert get a label
  appearance (`Gridfinity label RRGGBB`); a colored bin label stays bodies of its own, raised letters aren't joined to
  the bin, engraved and outline ones fill their cut flush. An exported 3MF has each of them as an object of its own in
  its color, ready to assign a filament in the slicer. The appearance is a library plastic copied and recolored,
  found by name in English or German (`Plastic - Matte`, `Kunststoff - matt`). Letters Fusion adds when a text is
  made longer later keep the default look, color them by hand or generate anew. Three new cases, colored cases check
  the look of their bodies.

### Changed

- The screw and hardware choices carry Cullenect's names („Round“, „T-Nut Side“, „Torx/Star“, ...) in Cullenect's
  order, new svg files come after them.
- The svg size of a symbol honours the units of `width` and `height`; a number without unit counts as CSS pixels as
  in the svg standard (was read as mm).
- „Dividers up to the top on grid lines“ moved to the „Bin compartments“ section and is only offered for a bin with
  more than one compartment. Saved defaults keep the setting.
- **Label command in a part design:** the document is switched to a hybrid design when the insert is generated (OK,
  not the preview), so the insert is a component of its own, and a small message says so. A part design takes a single
  component only; switching keeps its bodies, timeline and parameters, but a design with components can't go back to a
  part design. In an assembly design the insert is a component too (was a body in the root). New label case.
- The shape tests fail on a body left in a case's document that the generator didn't return, and a case can be built
  in a part design (`"designIntent": "part"`). Two new bin cases.
- **Dividers up to the top, rounded corners:** where a raised divider meets an outer wall or another raised divider,
  the corner is rounded up to the top like the compartment corners below: the corner's own rounding carries on, with
  the same radius and without a step, up the wall, round the chamfer under the lip and over the lip, so the chamfer
  runs on round it and ends at the divider. Before, the corner rounding stopped at the old top of the dividers and the
  rest of the corner was sharp. Bins of any size still stack on it. The shape tests fail on a ledge left where the
  rounding meets the corner below. New cases: 3x2 bin with 3 compartments and a Cullenect tab, with and without a
  scoop.

### Fixed

- **Insert lettering printable with a 0.4 mm nozzle (p130):** Joerg's slicer left parts of the insert text out,
  above all two lines („5mm“ over „Hex key“). Arial at the insert's text heights has strokes of 0.4–0.6 mm, a 0.4 mm
  nozzle lays 0.42–0.45 mm lines. The label dialog's „Bold“ switch is now a **Text style** choice: Regular, Bold or
  **Heavy** (Arial Black, the default for new inserts, about twice the stroke). Measured in Fusion on built inserts:
  M4x5 beside a screw 1.00 mm mean stroke (was 0.56), Joerg's „Welle 6mm“ 0.87 mm (was 0.52), two lines 0.76 mm (was
  0.39) and 99 % of it within reach of one line. Text and symbol are now **0.4 mm thick (two layers)** instead of one,
  raised or set in, on every surface; a full-height symbol set in now cuts through the top layer to the latch.
  Heavy runs about 20 % wider, a long text is fitted smaller by that. The text keeps its font when its text parameter
  changes. Test cases keep their font (`isBold` became `textStyle`), their snapshots changed only by the thickness;
  new case with two lines in Heavy.
- **Bin dialog opens again:** since the label color check of round 10 the bin dialog ran into endless recursion when
  opened (its state asked for the label color, which asked whether the bin is shaped, which built the state again):
  no bin could be made and the label tab inputs stayed greyed out. The color is now worked out from the finished
  state. A test checks that no dialog's state reaches itself again.
- **The root component stays active:** bin, baseplate and label commands activated the component they had just made,
  so Fusion showed every other component half transparent until the user switched back. The new component is active
  only while it is built, the design's root afterwards, also after a failed build. The shape tests fail on a case that
  leaves another component active.
- **Hint at thin text:** inserts and bin labels estimate the stroke from the fitted text height; text below 0.6 mm
  stroke (where a 0.4 mm nozzle starts leaving parts out) gives a message on OK and a note beside the preview time.
- **Screw choices without a symbol:** the label dialog offered every head, shaft, thread and driver together, head
  None with driver Hex had no svg and locked OK. Each dropdown now offers only what makes a symbol with the choices
  above it, a choice that doesn't moves to the first one that does; flange and security pin are locked where none
  exists.
- **Insert text on one line:** Joerg's 1U insert „Welle 6mm“ came out as two lines hanging over the insert. The text
  was fitted to exactly the width of its box by the outlines of its letters, Fusion breaks a box by their advance,
  which is wider. Each text line now stands on a fixed line of its own instead of in a box, so it never breaks, and
  fitting leaves 5 % of the width free. A text made longer later (`gfLabel1_text1`, `_text2`) is not fitted again: it
  stays one line and runs on to the right, towards the symbol and past the insert's edge, shorten it or generate the
  insert anew. Letters start after their side bearing, up to 0.5 mm further right than before. Shape tests check that
  an insert's text stays one band per line on the insert, and a case can set the text parameters after building; two
  new label cases.
- **Dividers up to the top:** with dividers that don't meet (3 compartments side by side), only the first went into
  the bin; the others stayed below the lip and their raised part lay loose in the design. Fusion doesn't join bodies
  that don't touch, so each raised divider is now joined to the bin on its own.

## Credits

- **Le0Michine** — [FusionGridfinityGenerator](https://github.com/Le0Michine/FusionGridfinityGenerator), the add-in
  this fork builds on, CC BY-NC-SA 4.0.
- **CullenJWebb** — [Cullenect Labels](https://github.com/CullenJWebb/Cullenect-Labels), insert and socket dimensions
  from `OpenSCAD/Cullenect.scad` (commit `d6dc0bb`), the symbols and the insert geometry and layout
  (`cullenect_base_v2`, `cullenect_label_generate`), MIT.
- **Set screw symbols** (`cullenectIcons/setscrews/`, `tools/setscrew/`) — own work of this fork, MIT, using
  Cullenect's thread and driver shapes (CullenJWebb, MIT).
- **ostat / Chris Heazlewood** — [gridfinity_extended_openscad](https://github.com/ostat/gridfinity_extended_openscad),
  reference for the Cullenect tab.
- **Pred** — [Gridfinity Storage Box v1.1 (parametric)](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric), size and shape of the
  storage box and its lid, rebuilt in code with changes, CC BY-NC.
- **Zack Freedman** — [Gridfinity](https://gridfinity.xyz).
