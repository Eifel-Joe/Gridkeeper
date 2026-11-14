# Changelog — Cullenect labels

Changes of this fork (`Eifel-Joe/FusionGridfinityGenerator`) on top of GridfinityGenerator v2.2.0.0.

## Unreleased

### Added

- **Label style „Cullenect“ for bins.** Every label tab, also each compartment tab and the tab of a shelled bin,
  gets a socket for exchangeable Cullenect label inserts instead of a printed label: 1.2 mm deep, 0.3 mm larger than
  the insert, with the latch ribs along both long sides. The socket takes the widest standard Cullenect width
  (`42 mm × n − 6 mm`, in half units) that fits the tab with 1 mm to spare, so original Cullenect inserts fit compartment
  tabs too. Its width is an expression on `gfBaseWidth` and it follows parameter changes like the labels do.
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
  units (following `gfBaseWidth`) or free in mm, a width and height correction like Cullenect's `offset_xy`. Text and
  symbol are one layer (0.2 mm), raised, set in or flush, and bodies of their own to print them in another colour.
  The width is a user parameter (`gfLabel1_width`), the symbol stays at the right edge when it changes. Each text line
  is a user parameter too (`gfLabel1_text1`, `gfLabel1_text2`) and stays live text, so it can be changed later like
  the bin labels; the font size is fitted when the insert is generated, a much longer text wraps in its box. All other
  sketches are fully constrained.
  Settings can be saved as defaults and shown with „Gridfinity settings“. Four label shape test cases.
- **Dividers up to the top on grid lines** (bin dialog, off by default): compartment dividers lying on a grid line go
  up to the top of the stacking lip. The feet of a bin stacked on top have a groove on every grid line, so a bin of any
  size still stacks on it, like a 4x2 on two 2x2. The dividers are cut by the feet of a stacked bin with clearance, so
  a divider a little off its line (dividers over many units are) or a thick one only keeps what fits. Dividers between
  grid lines (3 compartments on 4 units, half cells) stay below the lip. Hollow bins with a lip only; follows parameter
  changes. Two new bin cases.

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
  the corner is filleted up to the top like the compartment corners below: up the wall, round the chamfer under the
  lip and over the lip, so the chamfer runs on round the fillet and ends with it. Before, the corner fillets stopped
  at the old top of the dividers and the rest of the corner was sharp. Bins of any size still stack on it. New case:
  3x2 bin with 3 compartments, scoop and a Cullenect tab.

### Fixed

- **Dividers up to the top:** with dividers that don't meet (3 compartments side by side), only the first went into
  the bin; the others stayed below the lip and their raised part lay loose in the design. Fusion doesn't join bodies
  that don't touch, so each raised divider is now joined to the bin on its own.

## Credits

- **Le0Michine** — [FusionGridfinityGenerator](https://github.com/Le0Michine/FusionGridfinityGenerator), the add-in
  this fork builds on, CC BY-NC-SA 4.0.
- **CullenJWebb** — [Cullenect Labels](https://github.com/CullenJWebb/Cullenect-Labels), insert and socket dimensions
  from `OpenSCAD/Cullenect.scad` (commit `d6dc0bb`), the symbols and the insert geometry and layout
  (`cullenect_base_v2`, `cullenect_label_generate`), MIT.
- **ostat / Chris Heazlewood** — [gridfinity_extended_openscad](https://github.com/ostat/gridfinity_extended_openscad),
  reference for the Cullenect tab.
- **Zack Freedman** — [Gridfinity](https://gridfinity.xyz).
