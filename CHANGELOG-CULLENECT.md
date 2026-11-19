# Changelog — Cullenect labels

Changes of Gridkeeper (`Eifel-Joe/Gridkeeper`, until 16.11.2026 `Eifel-Joe/FusionGridfinityGenerator`) on top of
GridfinityGenerator by Le0Michine, merged up to ee027a9 (v2.5.0.0, 17.11.2026; rounds 1 to 11 were built on v2.2.0.0, round 22 merged v2.4.2.0, round 38 v2.5.0.0).
Gridkeeper counts its own versions from 1.0.0; its tags are `gridkeeper-vX.Y.Z`, the `vX.Y.Z.W` tags belong to GridfinityGenerator.

## 1.2.0 (2026-11-19)

### Raised dividers with a pointed top, and fixes around scoops (round 50)

- **Dividers up to the top stay on their grid lines beside a scoop wall:** a wall with a scoop starts the
  compartments along it at the lip's inner edge. Until now the whole compartment grid moved with it, the dividers
  lay up to 1.2 mm off their grid lines under a full lip (0.75 mm under a light one), and the feet of a bin stacked
  on top cut their raised part away on one side: narrow ridges, steps and gaps in the lip at every divider (p650).
  This already happened with the bin's front scoop and became easy to reach with the scoops per compartment of
  round 48.
  - Decided: with dividers up to the top the grid is laid out from the walls as without a scoop, and only the
    compartments along a scoop wall are shorter by its inset (1.4 mm under a full lip, 0.7 mm under a light lip with a
    1.2 mm wall). Bins without raised dividers keep the evenly spaced compartments of round 48.
- **Raised dividers end in the lip's top shape:** decided, a divider on a grid line goes straight up to the lip's top
  as thick as it is and no longer ends flat with two right angles (round 8). Under an untrimmed lip its top is a roof
  with the lip's 45 degree slopes, its ridge at the lip's top; under a trimmed lip a flat top at the trimmed top,
  chamfered at 45 degrees on both sides by 0.3 mm (0.6 mm flat on a 1.2 mm divider, as wide as the lip's crown).
  The feet of a bin stacked on top keep their air. Saved bins rebuild with it.
  - The corners where a raised divider meets a wall or another divider are rounded from the compartment's corner up
    over the wall and the lip to the top, as in round 8 (p83). Under a full lip the rounding starts where the lip's
    support leaves the wall, which also takes away the support's kinks beside the divider.
  - Two other shapes were built and dropped: the lip's whole profile and the lip's top contour on both sides of a
    divider, both wider than the divider.
- **No gap between a raised divider and its wall:** at a scoop wall the raised divider ended half a wall short of the
  cavity at the lip's inner edge, and under an untrimmed lip at the wall's middle; near the top of the lip, which is
  thinner there, a gap of up to 1.1 mm was left (already so before round 50). The raised dividers now reach the outer
  walls up to 0.1 mm under their outer face, shaped there by the feet of a stacked bin like the lip.
- **Shape tests check for gaps:** every bin case with compartments is cut in the plane of each divider and beside it;
  a gap of 0.2 mm or more between a divider and its wall at any height fails the case.
- **No ledges where raised dividers cross (p651):** the compartment corners there are rounded up to the top like
  those at the walls.
- **A bin one unit high with a scoop builds (p652):** the floor fillet beside a scoop is at most the cavity's depth
  less 0.1 mm; at 1 mm depth the full 2.55 mm failed in Fusion.
- **No ledge between two scoop walls (p653):** a cavity corner where two scoop walls meet is concentric with the lip's
  inner corner (1.15 mm under a full lip, 1.85 mm under a light one, with the default 1.2 mm wall) instead of leaving a level face of 1.1 mm².
- **Shape test cases:** seven new bins (raised dividers beside scoop walls under a full and a light lip, crossing
  raised dividers, a bin one unit high with a scoop, two scoop walls with raised dividers); all sixteen cases with
  raised dividers and four round 48 cases with two scoop walls stored anew.

### Box small parts kept on disk (round 49)

- **The first box after Fusion starts is fast too:** latch, hinge and handle pin, once drawn, are also kept as .smt
  files (with their body names in a .json) in the folder `partCache` of the add-in folder, beside `updateConfig`.
  The first box of a Fusion session reads them instead of drawing them. Measured in Fusion: the three parts 1.3–1.4 s
  instead of 27–30 s, box 5×4×6 built in 50 s instead of 78 s; further boxes in a session unchanged (about 1 s).
  - The parts are still drawn in code; the files are only a store the add-in writes and reads itself, no part file
    ships with it (decided: build it, the rule "parts drawn in code, never imported from a part file" holds).
  - Keyed by the add-in version and a hash of the drawing code (`lib/gridfinityUtils`), so a code change without a
    version step reads no stale file; files of other keys are deleted when new ones are written.
  - A missing, unreadable or broken file is drawn anew and written again; a failed write is only logged, the box is
    built either way. An update does not carry the folder over, git ignores it.
  - Same geometry: box snapshot cases pass with parts drawn and with parts read (p610).

Box and small parts after Pred's parametric Gridfinity Storage Box (Printables 543553, CC BY-NC).

### Box small parts (round 47)

- **Small parts of the box from the session, not drawn anew in every box:** latch, hinge and handle pin are drawn
  once per Fusion session and every box set gets copies of their bodies, as one base feature in each part's
  component (decided: they need no parameters and no history). Measured in Fusion with the same document steps:
  the second box 84 s instead of 139 s; in a rebuild and in every further box the three parts take about 1 s each
  instead of 8–20 s; a box brings 761 model parameters instead of 877. The first box of a session draws them once,
  as fast as before (p591).
  - The handle is still drawn in each set and follows the box width through its parameter.
  - Same names, places and joint origins as before: the parts sit on their seats, joints of the user on a latch or a
    handle pin move to the rebuilt set, export and colour are unchanged.
  - The parts are drawn by their generators into a scratch component of the set that is deleted again (a hidden
    helper document is not available in Fusion's API); if copying fails, the part is drawn in its component as
    before and the reason logged.
- **Box snapshot cases:** six cases stored the latch's area from before the latch was drawn in code (3085.727768
  instead of 3085.723822 mm², same volume); their latch is stored anew, so they pass again (p592).

Box and small parts after Pred's parametric Gridfinity Storage Box (Printables 543553, CC BY-NC).

### Faster joint origins for bins, baseplates and inserts (round 46)

- **Bins, baseplates and inserts build and rebuild faster:** their joint origins (the sockets of a baseplate, the
  feet, the pocket and the cell placement of a bin, the joint origin of an insert) sit on the component's origin with
  offsets that follow the parameters, as the box's since round 45, instead of each having a construction plane, a
  sketch, a point and two dimensions of its own (p590). Measured in Fusion with the same steps in a new document
  (baseplate 6×6, a 2×1×3 Cullenect bin in socket 2-2, an insert in its pocket, each rebuilt, then the baseplate's
  base width 42 → 50 mm): baseplate 5.6 s instead of 9.7 s, its rebuild 12.0 s instead of 27.7 s; bin 7.4 s instead
  of 9.5 s, its rebuild 8.3 s instead of 11.4 s; insert 2.9 s instead of 3.5 s, its rebuild 2.3 s instead of 3.5 s.
  The baseplate brings 220 model parameters instead of 294, so every later item in the document gains too.
  - Same place, same axes, same behaviour on a parameter change: the bin stays in its socket and the insert in its
    pocket through every rebuild and the width change.
  - Items already in a document keep their sketch joint origins until they are rebuilt; a rebuild makes the new
    kind and moves the joints over by name as before (checked with items built by the code before this round and rebuilt with this one).

### More scoops (round 48)

- **A scoop on every wall:** the bin dialog's scoop group has a checkbox for each wall (front, back, left, right)
  instead of the single front scoop; every compartment gets a scoop at each wall checked. Idea: teateatea, upstream
  issue #140 (two scoops for long parts, four for small parts, three beside a label tab).
- **Scoops per compartment:** the compartment layout editor has a Scoops row for the selected compartment; with Own
  it chooses that compartment's walls alone, without it takes the bin's. Merge and split keep the choice, the drawing
  marks the scooped walls.
- Decided: the back wall carries the label tab and is locked while a tab is chosen, for every compartment since each
  carries its own tab; without a tab four scoops are possible. Compartments without a choice of their own follow the
  same rule as the single scoop before, only on more walls.
- Decided: two scoops facing each other in a compartment have their radius limited to half its span less 0.5 mm, a
  strip of flat floor stays; Scoop max radius stays the upper bound, a single scoop per axis keeps its old limit.
- A compartment with more than one scoop has no rounded floor edge at its other walls: Fusion fails to round a
  floor edge running into two different scoops.
- Scoops on walls that meet blend at the corner. With a lip, every scoop wall reaches up to the lip's inner edge and
  the lip bottom chamfer leaves it out; creases leave every scoop wall out.
- A bin with only the front scoop is built as before, and saved settings without the new walls load with the front
  scoop alone.

### Box build speed (round 45)

- **Box build and rebuild faster:** measured in Fusion with the same document steps back to back (box 5×4×6 with
  its small parts, a second one beside it, the first rebuilt as 6×4×6 with two joints of the user on its parts, a
  preview, a rebuild preview): the first box 75 s instead of 115 s, the second 147 s instead of 214 s, the rebuild
  316 s instead of 471 s, the preview 123 s instead of 197 s, the rebuild preview 143 s instead of 232 s. A box
  brings 877 model parameters instead of 965, so every later box in the document gains too (p296, p480).
  - The box's joint origins (cells, stacking, lid, the seats of the small parts) sit on the component's origin
    with offsets that follow the box parameters, instead of each having a construction plane, a sketch, a point and
    two dimensions of its own: same place, same axes, same behaviour on a parameter change.
  - A sketch dimension between two points that hang on the same measure never changes; it keeps its value instead
    of getting an expression (129 of 215 per box).
  - Chamfers and fillets look their edges and faces up where they are expected instead of reading every edge of the
    box (about 34 000 per build); when one isn't found that way, the whole body is read as before and the add-in
    log says so.
  - The box label of a rebuilt box finds the front of the box through its joint origin's position, which counts
    those offsets.
  - Boxes already in a document keep their joint origins as they are until they are rebuilt. Bins, baseplates and
    inserts keep their sketch joint origins for now.

### Privacy note

- `documentation/PRIVACY_POLICY.md` was GridfinityGenerator's generated policy for the Autodesk App Store (website,
  cookies, accounts, Canadian law) and didn't describe Gridkeeper. It is replaced by a short note of what Gridkeeper
  actually does: it collects no data; the daily update check asks GitHub for the releases and can be turned off;
  updates, error reports and links go to GitHub or the site they name. The same note is in the documentation under
  Reference › Privacy.

### Component names after a rebuild (round 44)

- A rebuilt part's component was named with Fusion's counter, e.g. a bin rebuilt without a cell became
  "Gridfinity bin 1x1x3 (1)", and "(2)" after the next rebuild. Fusion numbered the new component because the old
  one still existed. Once the old part is gone, every component the rebuild made gets its name back without the
  counter, or the lowest free one if another part holds the name. This covers bin, insert (and its Text component),
  baseplate, box and box label rebuilds. Components that existed before the rebuild keep their names, the user's own
  with an "(n)" included. A name the generator asks for with an "(n)" of its own, like an insert whose text ends in
  "(2)", is kept too: only a counter Fusion added to the requested name goes (p570).

### Typed values in the dialogs (round 41)

- A value typed into an input and OK clicked straight after (within about 0.3 s) was ignored: Fusion takes typed text
  only a moment after the last key, and neither reports the change nor gives the new value on OK, measured for every
  kind of input (spinners, lengths, sliders, text). No other kind of input avoids it, so nothing changes in the
  dialogs; the FAQ says to press Tab or wait a moment before OK. Decided: documented, not worked around
  (p490).

### Faster deletion of the old part on a rebuild (round 43)

- **Rebuild with joints moved over:** when a rebuild moves joints to the new part (a bin in a cell of a rebuilt
  baseplate or box, an insert in the pocket of a rebuilt bin, a box label or a joint of the user on a rebuilt box),
  the old part used to be deleted item by item. Deleting it in one go dropped the moved joints: they still depended
  on the old joint origin they had used. Now those few joint origins go first, then the rest in one go, and the
  joints stay. Measured in Fusion: deleting the old box of a 5×4×6 box rebuilt as 6×4×6 with two joints moved took
  21 s instead of 252–274 s, and the whole rebuild 254 s (727 s in the round 39 measurement). A baseplate with a bin
  in a cell took 0.6 s instead of 2.7 s, a bin with an insert 0.9 s instead of 5.4 s. Where the one-go delete
  can't be trusted (a joint origin not found or not deleted, the old items not in one piece, the delete refused),
  the code deletes item by item as before and writes so to the add-in log. Bin, insert, baseplate, box and box label
  rebuilds share this code; the box label rebuild wasn't measured (p533).
- **Joint names after a rebuild:** a bin rebuilt in its cell had its joint named "… in cell (1)", and "(2)" after
  the next rebuild; inserts got "… in pocket (1)". Fusion numbered the new joint because the old one still existed.
  Once the old part is gone, the joint the rebuild made gets its name back without the counter, or the lowest free
  one. Joints that existed before the rebuild keep their names, the user's own included (p430).

### Box speed (round 39)

Box after Pred's parametric Gridfinity Storage Box (Printables 543553, CC BY-NC, by Pred), drawn in code.
- **Faster box build:** every Fusion call gets slower the more model parameters a document holds, and every sketch
  dimension is one. Sketch points that hang on no box size are now fixed in place instead of held by two dimensions;
  points on the box's width, length or height keep their dimensions, so changing those parameters still resizes the
  box. A box brings 965 parameters instead of 1409 (450 sketch dimensions instead of 894), every sketch stays fully
  constrained and the shape is unchanged. Edges are read by index, which halves those calls. Measured in Fusion, the
  same session and document layout before and after: the first box 141 → 110 s, a second box beside it 271 → 213 s,
  the preview 218 → 182 s, a rebuild with two joints moved over 792 → 727 s (most of a rebuild is deleting the old set
  item by item, unchanged). Decided: the ends and centres of arcs keep their dimensions, Fusion rejected fixed points
  around concentric arcs as over-constrained (p296, p480).
- **Rebuild preview:** the old set is hidden by switching its light bulb off instead of suppressing its timeline group,
  which Fusion always refused for a box (the log said "Cannot suppress/unsuppress group", then every item was suppressed
  one by one). The preview of a rebuild takes 286 → 219 s. The light bulb is switched back on whenever the dialog
  closes; a set hidden by hand before stays hidden (p481).
- **Rebuild with joints of the user:** rebuilding a box with a joint of the user on it broke off with
  "InternalValidationError : jointOcc" when further joints came after it in the timeline, a second box for example.
  The joints are now read before any is moved; the same for an insert's pocket joint when a bin is rebuilt (p530).
- **Snapshot tests:** a case whose build breaks no longer leaves its half-built document open (p531).

### Faster symbols (round 40)

- **Symbols of lines and arcs:** OpenSCAD writes every rounding of a symbol as a polygon, the Torx drive of a
  countersunk screw was 1670 points 0.01 mm apart. The symbol files are rebuilt as lines, circular arcs and whole
  circles within 0.01 mm of the polygons: 239 064 points became 19 145 lines and 1 890 arcs, the Torx symbol 54
  segments (p371). The symbols of Cullenect-Labels by CullenJWebb (MIT) keep their origin and license, the rebuild is
  noted next to them; the tool is `dev-notes/tools/arcSymbols.py`, the render tools run it after rendering.
- **One import per symbol:** a symbol was imported four times to measure and place it, five times on bin labels. It is
  imported once now, scale and position worked out from the file. Measured in Fusion: a box label with the
  countersunk Torx symbol 40.9 s → 0.8 s, an insert with it 40.4 s → 1.1 s; on a bin label the symbol takes 0.6 to
  0.7 s instead of 1.8 to 3.7 s.
- Two insert test cases build their symbol a few hundredths of a percent different in volume, round instead of
  faceted; their snapshots are updated. A hand-made svg in the symbol folders, drawn with other commands, circles or
  transforms, still works in the add-in: it is imported once and scaled into place; the tool leaves such a file as it
  is.

### GridfinityGenerator 2.5 merged (round 38)

Merged from GridfinityGenerator v2.5.0.0 by Le0Michine (Lev Mishin), up to ee027a9 (p13):
- **Magnet socket chamfer:** bin and baseplate magnet sockets get a 0.5 mm chamfer around their opening, so magnets
  go in easier and the first layer doesn't squish into the hole (by Le0Michine).
- **Connection holes:** only skeletonized baseplates get them, the dialog greys the inputs out for light and full
  plates; a padded side gets none, like a side with half cells (by Le0Michine).
- **Position of a new bin:** *Snap to free spot* or *Center on origin*; a centered bin is centered again when rebuilt
  (by Le0Michine). Decided: it joins the fork's cell placement in one **Placement** group, always shown, the dropdown
  called **Position**. A picked cell wins and greys the position out, then Center on origin, then the spot a rebuilt
  bin had, then the free spot.
- **Tab top offset:** how far the label tab is below the top of the bin, 0 to 2 mm, 0.5 mm by default; the dividers
  between compartments are lowered as much (by Le0Michine). The fork's dividers up to the top and Cullenect pockets
  follow the offset, so they still meet the lowered dividers and tab.
- Settings files and bins of older versions without the new settings build as before: *Snap to free spot*, offset
  0.5 mm (round 32 rule).
- Decided: the original's `FUNDING.yml` (donation button) is not taken. Its wiki pages and pictures stay out of the
  fork, the documentation is under `docs/`.

### Each label color on a filament of its own (round 37)

- **Label filaments in the export dialog:** the 3MF export painted all label text with one filament, red and blue
  text alike. It now gives each label color a filament of its own: the parts print on filament 1, the first color on
  2, the next on 3 and so on, label text without a color counting as one more color (p301). The dialog lists the colors
  of the selected parts under **Label filaments**, such as *Red text* and *Blue text*, each with a list of filaments 1 to 18;
  a number picked there is kept for the next export. The single **Label color index** is gone; the index an earlier export
  saved stays the filament of label text without a color, so outline labels print as before.
  Decided: automatic numbers that can be changed in the dialog and are remembered. The color is the one Gridkeeper
  gave the text; text recolored by hand in Fusion counts as text without a color.

### Box rebuild and preview (round 36)

- **A joint on a small part stays on it:** a joint of yours on one of the four latches, a handle pin or a hinge of a
  box went to the last latch (pin, hinge) when the box was rebuilt (p293). The four latches are one component; the
  rebuild now tells them apart by the seat the set joints each of them to, *Latch front left* and so on. A part
  that isn't jointed at its seat any more can't be told apart; its joint stays with the old set and the rebuild says so.
- **Preview without the small parts:** the box dialog's preview builds box and lid only, the small parts come with
  OK (p295); inserting them made every preview slow. The checkbox's tooltip says so. Box after
  [Pred's storage box](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric)
  (CC BY-NC, by Pred).
- **Lighter box preview (p296):** the preview makes no joint origins either (cells, stack, seats, lid), OK makes
  them all; in a Fusion measurement they had taken up to 75 s of a preview. The box build and rebuild themselves
  aren't faster: most of their time is Fusion recomputing a design that grows with every box. The hinge looks up its
  chamfer edges from one list of the edges instead of walking them all again for each edge.

### Label tab of a shelled bin under a lip (round 34)

- **p281, checked: the tab sits on the back wall under either lip:** a shelled bin builds no scoop, so the front
  placement of its label tab at the light lip's inner edge (inherited from GridfinityGenerator by Le0Michine) could never
  run, and the tab never sat at the wrong edge under a full lip. The dead branch is removed; the tab is placed by
  `shelledTabOriginY`. New snapshot case `bin_2x1x3_shelled_lip_full_scoop_tab`.

### Closed box lid (round 30)

- **Lid top: Grid or Closed:** the box dialog has a group *Lid* with **Lid top**. *Closed* builds the lid flat and
  closed on top instead of with a Gridfinity grid, sturdier; the stacking tabs in its corners stay, so boxes still
  stack (a box stands on its lid, and the tabs in the lid's corners reach into the box's floor). The default stays the
  grid, and boxes saved before the choice rebuild with it.
  Underneath both lids are the same and hold the bins alike. The box follows
  [Pred's storage box](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric)
  (CC BY-NC, by Pred); the closed top is Gridkeeper's change to it.

### Older bins build as they were saved (round 32)

- **No settings a config doesn't give:** a bin, baseplate or box saved before a setting existed takes the value that
  built it on Load from file, rebuild and clone, not the one the dialog has (p280: older bins are built as they were saved, no setting is
  switched on that the config doesn't give). Bins:
  sharp shell, no dividers up to the top, no label color, 0.3 mm play of a Cullenect insert, light lip trimmed flat as
  before. Baseplates: the bin xy clearance at the edges where plates meet, as before they had a clearance of their
  own. Configs of GridfinityGenerator by Le0Michine build the same way.
- **Changes p151 (round 18):** an old bin with a label used to keep the label color chosen in the dialog, it now
  comes without one and the dialog shows *None*. A file with only some settings gets these older values too; the
  settings every config had since 13.11.2026 still keep the dialog's value when a file leaves them out.
- **Plate edge clearance up to 0.5 mm:** the largest bin xy clearance, so baseplates saved before the plate edge
  clearance build the same with any xy clearance (it stopped at 0.25 mm, half the whole gap of upstream's setting;
  nothing in the geometry needs that).
- **Not reproduced:** a fill area baseplate saved on 13 or 14.11.2026 with the fit tolerance GridfinityGenerator
  removed since (3010f3f, Le0Michine) builds 1 mm larger along each axis (its default tolerance), the setting is
  reported as not recognised. Older than 1.0.0, nobody else had the add-in then.

### A new bin into a cell (round 31, p312)

- **Cell in the bin dialog:** a new section **Placement** picks a cell joint origin of a baseplate or of the floor of
  a box, the new bin is jointed into it (joint *… in cell*), as inserts are into their pockets. A bin larger than
  1 × 1 goes there with its front left cell. Without a baseplate or box in the design the
  section isn't there and the bin is built beside the others as before. Offered are the cells of every baseplate
  and the floor cells inside a box, not the grid on its lid; only for new bins.
- **Rebuilt bins keep their cell:** a rebuilt bin is jointed into its cell again, a bin whose parameters are only
  set keeps its joint anyway. The bin has a joint origin of
  its own for it, *Cell placement joint origin* at its front left cell, also in a half grid.
- **Boxes always have their cell joint origins:** the box dialog's **Add joint origins** is gone, every box gets a
  joint origin in each floor cell. A box built without them gets them when it is rebuilt; only joint origins are
  added, its geometry stays the same. The box is after
  [Pred's storage box](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric)
  (CC BY-NC, by Pred).
- **Rebuilt baseplates keep their bins:** a baseplate rebuild moves the joints on its socket joint origins over to
  those of the same name, as the box rebuild does; before, a bin jointed into a socket lost its joint.

### Reload Gridkeeper, developer commands in git worktrees (round 33)

- **Reload Gridkeeper:** after an update Gridkeeper asks „Reload Gridkeeper now to use it?“, and the Gridkeeper updates
  dialog has a Reload Gridkeeper button whenever the version on disk isn't the one running, also in a git checkout
  after a pull or a branch switch, where Fusion doesn't load the new code by itself. Gridkeeper stops and runs
  itself through Fusion's API once its dialogs are closed; measured 18.11.2026 that every command works afterwards.
  Restarting Fusion, or Stop and Run in Scripts and Add-Ins, still work and are named when the reload fails (p321).

- **Developer commands in a git worktree:** the snapshot tests and the model images command show whenever the add-in
  runs from a git checkout, also from a git worktree, where `.git` is a file instead of a folder. They use the same
  check as the update lock (p320).

### Trim sketches fully constrained (round 35)

- **Shaped bins and baseplates:** the sketches *Outer clearance trim sketch* (bins with a shape, e.g. an L-shape or
  a shape in half cells, p282) and *Plate outline trim sketch* / *Plate pieces cut sketch* (baseplates, p290) are
  fully constrained now. The frame around the outline, whose region the cut takes, had no position or size; it is
  dimensioned from the sketch origin like the other rectangles of the generator. The geometry stays the same. Both
  sketches came from GridfinityGenerator by Le0Michine.

## 1.1.0 (2026-11-17)

### Export in print orientation (round r29-export)

- **Parts in print orientation:** the 3MF lays every part the way it is printed instead of where it is in the design:
  the box set's handle flat, its latches flat, the Pinned hinge's pin on its flat side, Cullenect inserts on their
  underside and Flush ones on their text; bins, baseplates, box, lid and hinges as designed. The box parts follow
  [Pred's storage box](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric)
  (CC BY-NC, by Pred). STL files come in print orientation too, STEP stays as designed.
- **Print bed, spacing, purge tower:** the export dialog picks the bed (the baseplate dialog's printers or a size of
  its own), the spacing between the parts (5 mm) and, with colored label text, a square kept free for the purge tower
  (50 mm). The parts are spread over the bed, what doesn't fit goes on further plates, a 3MF file per plate
  (a sorting only works properly with one 3MF per plate), so the slicer keeps
  its printer, filament and process settings. The choices are kept.
- **Bambu Lab printers apart (click test):** the printer list of the export and baseplate dialogs has every Bambu
  Lab printer of Bambu Studio's profiles, the old *Bambu Lab A1, P1, X1* entry is split (a baseplate saved with it
  opens as *Custom* 256 × 256). The export keeps the purge tower's square where Bambu Studio puts the tower and,
  for the P1 and X1, keeps clear of their excluded corner, which made Bambu Studio warn of collisions.
- **Parts as a compact group:** the parts of a plate lie as a roughly square group in the middle of the bed, not in
  a row across its whole width.
- **A box set on three plates:** box, lid and small parts each on plates of their own, so a box comes to three plates
  depending on its size.
- **Pinned hinge's halves named after it:** *BottomHingePart_Pinned*, *TopHingePart_Pinned* (Pred names them like the
  M3x30 hinge's).
- **Box label is a part of the export (p380):** All Gridkeeper parts takes the box label with its text, a Flush label
  lies on its text.

### Joint origins explained

- [Joint origins](docs/working/components.md#joint-origins) is now a guide: which joint origins every model has, how to pick one
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
  are; latches, hinge, handle and pins get a colour other than the box and lid.

### Box label (round 29)

- **Gridkeeper box label (p262):** a new command makes the label for the holder of a box after
  [Pred's storage box](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric) (CC BY-NC):
  Pred's flat plate sized after the box's width, a large text at the left, two lines and up to five
  [Cullenect](https://github.com/CullenJWebb/Cullenect-Labels) symbols (MIT, CullenJWebb) at the right, raised, set in
  or flush like the Cullenect inserts. Picking the *Label joint origin* of a box joints the label into its holder; every
  box now has that joint origin. A command of its own, so a label can be swapped without touching the box. Every
  sketch is fully constrained.
- **Settings, rebuild and clone for the box label:** the box labels lacked the Gridkeeper settings, rebuild and clone
  entries of the right-click menu that the Cullenect labels have. Now they do,
  like the Cullenect inserts: the label keeps its settings, a rebuild builds it anew in place and jointed into the
  holder of its box again, a clone opens the dialog with its settings and no box.
- **The holder stays shown:** after a rebuild without its box the box's *Label joint origin* was hidden; no Gridkeeper
  code turns joint origins off, the ones a joint had used were off. The joint origin must not be hidden. The box label and the Cullenect insert now keep the holder or pocket they are jointed into shown, also
  when a rebuilt box or bin takes the joint over, and a rebuild shows the one the old label or insert leaves.
- **A rebuilt box keeps its label:** the label's joint moves over to the *Label joint origin* of the rebuilt box.
  A label too wide for the rebuilt box is taken out and laid flat in front of the box, 10 mm in front of the handle and
  centred on the box (in front of the front it is easy to see); is something in the
  way there, it goes to a free spot beside the parts. A narrower one stays in; the note after the rebuild says where
  the label is and to rebuild it with the new width.

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
- **Label icon keeps its full size** (as in the original): only the text shrinks to the width left after the
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
  standard (thicker is fine, thinner not). Below it the bin dialog keeps OK locked and says why in the
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

- **Insert lettering printable with a 0.4 mm nozzle (p130):** A slicer left parts of the insert text out,
  above all two lines („5mm“ over „Hex key“). Arial at the insert's text heights has strokes of 0.4–0.6 mm, a 0.4 mm
  nozzle lays 0.42–0.45 mm lines. The label dialog's „Bold“ switch is now a **Text style** choice: Regular, Bold or
  **Heavy** (Arial Black, the default for new inserts, about twice the stroke). Measured in Fusion on built inserts:
  M4x5 beside a screw 1.00 mm mean stroke (was 0.56), the insert "Welle 6mm" 0.87 mm (was 0.52), two lines 0.76 mm (was
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
- **Insert text on one line:** A 1U insert "Welle 6mm" came out as two lines hanging over the insert. The text
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
