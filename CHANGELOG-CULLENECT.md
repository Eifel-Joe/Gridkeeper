# Changelog — Cullenect labels

Changes of this fork (`Eifel-Joe/FusionGridfinityGenerator`) on top of GridfinityGenerator v2.4.0.0 (rounds 1 to 11 were built on v2.2.0.0).

## Unreleased

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
- Known limit: colored label bodies have no tag of their own, a feature after the bin that uses one of them has to
  pick it again after a rebuild (Fusion reports it).
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
- **Zack Freedman** — [Gridfinity](https://gridfinity.xyz).
