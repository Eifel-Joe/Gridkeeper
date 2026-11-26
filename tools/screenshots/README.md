# Pictures for the docs

The model pictures of the docs (`docs/assets/models`) are made from the presets in `models/`, by the palette
**Gridkeeper docs: render models** in Fusion or by a script; the animations (`docs/assets/gif`) by
`dev-notes/tools/anim/compose.py`, see `docs/assets/images/NEEDED.md`. The dialog screenshot tool below comes from
GridfinityGenerator and writes to `tools/screenshots/out/` (ignored by git).

## Dialog screenshots

Screenshots of the bin and baseplate dialogs for the docs and release notes, in Fusion's dark and light themes, without
opening Fusion. Each command's own `command_created` runs against a fake of the Fusion API (`fakeAdsk`), so the inputs,
their values, what's enabled or hidden and what the drawings show all come from the add-in's code. `page/dialog.js` draws
the dialog the way Fusion does, with the add-in's own pages in it, and a headless browser captures it.

## Setup

The tools outside Fusion need a Python with Pillow, the dialog screenshots Playwright too, both from PyPI. Either a
venv of the tool:

```sh
python3 -m venv tools/screenshots/.venv
tools/screenshots/.venv/bin/pip install -r tools/screenshots/requirements.txt
```

(on Windows `py -3 -m venv tools\screenshots\.venv` and `tools\screenshots\.venv\Scripts\pip install -r
tools\screenshots\requirements.txt`), or `pip install pillow playwright` into the computer's Python. The palette takes
the first of: the checkout's `tools/screenshots/.venv`, for a git worktree the main checkout's, then `py -3`, `python`,
`python3`, each only when it imports what the tool needs (`commands/commandModelScreenshots/screenshotTools.py`); a row
says which Python is missing. Playwright uses the installed Google Chrome.
The dialog font, Artifakt Element, is taken from the Fusion install. Use `--font-dir` to point to it if it isn't found.

### Taking shots

```sh
tools/screenshots/.venv/bin/python tools/screenshots/screenshots.py                  # every shot in shots.json
tools/screenshots/.venv/bin/python tools/screenshots/screenshots.py --only bin-custom-shape-drawing --themes dark
tools/screenshots/.venv/bin/python tools/screenshots/dialogRecorder.py bin           # the inputs a shot can set
tools/screenshots/.venv/bin/python tools/screenshots/screenshots.py --language de    # German, name.de.png beside the English
```

With `--language de` the add-in's texts are German (`lib/i18n/de.json`), also the add-in's items of a right-click menu;
the pictures are named `name.de.png` (`name-dark.de.png`), as the German docs pages find them.

A shot in `shots.json`:

| Key | |
|---|---|
| `name` | File name, with `-dark` or `-light` added when it is taken in both themes |
| `command` | `bin`, `baseplate` or `export` |
| `menu` | Instead of a command, Fusion's right-click menu with these `items`, each a `label` with an optional `shortcut` and `icon`, a file from the add-in folder or `eye`, or `{"separator": true}`. `"cutTop": true` tears the top, for a menu going on above. `"hover": true` on an item lights it. `scene` opens the menu on Fusion's viewport, `{"width", "height", "model": {"picture", "x", "y", "width"}, "menuAt": [x, y]}` in dialog pixels, a model picture from the add-in folder, the menu's corner can be above the viewport's top, the pointer rests on the hovered item, at `cursorAt`, shares of its label's width and height. Fusion's own icons aren't drawn, the add-in's are |
| `values` | Input values by id, as the dialog saves its defaults. Lengths are in cm, or a string such as `"42 mm"`. Groups take `true` or `false` to expand or collapse them. The export keeps no defaults, its values are set once the dialog is up: a selection takes how many bodies are selected, a text box its text |
| `globals` | Values of the command's other state, such as `binShapeCells` or `compartmentPockets` |
| `defaults` | A saved `ui_input_defaults.json` to start from instead of the original defaults |
| `inputs` | Input ids to show. The shot takes the part of the dialog from the first to the last of them and tears the edges where it is cut. `<group id>:header` is the header of a group. Leave it out to take the whole dialog |
| `edge` | How cut edges look: `zigzag`, even teeth, the default, `wave` or `rough`, long uneven tears |
| `torn` | `false` for straight cut edges |
| `margin` | Space kept around the inputs, 10 px by default |
| `height` | Limits the dialog to this height and shows a scrollbar, like the dialog in Fusion. By default the whole dialog shows |
| `width` | Dialog width, as the command sets it by default |
| `themes` | `["dark"]`, `["light"]` or both, the default |
| `scale` | Pixels per dialog pixel, 2 by default |
| `output` | Folder for the images, from the add-in folder |
| `steps` | Makes the shot an animation, see below |
| `format` | `gif`, the default, or `webp` for an animated WebP with a transparent background |
| `background` | Color behind the dialog, GIFs default to GitHub's page color of the theme, as they can't fade a shadow into transparency |

### Animations

A shot with `steps` is a GIF of a cursor going through them. The dialog reacts through the command's own handlers and
the drawings are the add-in's pages receiving real mouse and keyboard input, so what changes, enables or shows up is
what Fusion would do. The frame stays the same size for the whole animation, large enough for the inputs at their
largest. Each step has one action:

| Step | |
|---|---|
| `{"click": "custom_shape"}` | Clicks a checkbox, a button or a group header, by input id |
| `{"click": {"page": "shape_browser", "selector": "#fill"}}` | Clicks something on a page, by CSS selector |
| `{"spin": {"input": "bin_width", "direction": "up", "times": 2}}` | Clicks a spinner arrow |
| `{"select": {"input": "bin_type", "item": "Shelled"}}` | Opens a dropdown and picks an item |
| `{"type": {"input": "bin_wall_thickness", "text": "0.8"}}` | Types in a field, in the input's units |
| `{"type": {"page": "compartments_browser", "selector": "input[type=text]", "text": "Screws"}}` | Types in a field on a page, then presses Enter unless `"enter": false` |
| `{"drag": {"page": "shape_browser", "selector": "svg", "from": [0.9, 0.1], "to": [0.9, 0.5]}}` | Drags on a page, from and to are fractions of the width and height of the selected element |
| `{"move": {"input": "bin_height", "part": "field", "at": [0.8, 0.5]}}` | Moves the cursor. A part is `field`, `checkbox`, `button`, `up` or `down` |
| `{"key": "Escape"}` | Presses a key on the focused page |
| `{"set": {"bin_height": 6}}` | Changes inputs without the cursor |
| `{"wait": 800}` | Holds the frame for some milliseconds |
| `{"cursor": false}` | Hides the cursor, `true` shows it again |
| `{"model": 2}` | Marks that a GIF of model pictures shown beside this one goes to its third picture as the dialog last changed, see below |

## Model pictures

Pictures of bins, baseplates, boxes, box labels and label inserts come from Fusion itself: with the add-in running from
a git checkout, Utilities > Add-ins has a **Gridkeeper docs: render models** button. It opens a palette docked on the right listing every preset
in `models/` with its saved picture, or **No picture**. **Create** or **Refresh** makes a preset's picture, **Refresh
all** makes every one and then the GIFs below, **Make GIFs** only the GIFs, **Open location** shows the folder of the
pictures in Finder or Explorer; presets are read again from their files each time, and clicks while pictures are being made
wait their turn. Click a picture to see it large, **Open file** opens it in the computer's image viewer.

A picture is made by building the preset in a new document with the add-in's own builders, hiding everything but the
bodies, setting up the view in Fusion's Photo Booth lighting and saving it, by default to
`docs/assets/models/<preset>.png`, where the pages take it. The document is closed without saving.

The palette also finishes the pictures, Fusion's Python has no imaging. Fusion renders the view at the viewport's
proportions and `supersample` times the picture's size, the palette's page cuts that to the model, fits it in the
picture with `margin` around it and scales it down, which smooths the edges. When the model touches an edge of the
render the camera moves back and renders again, up to 3 times; a picture still touching is saved and marked as
possibly cut off.

Each preset's result, with the full error of a failure, is written to `tools/screenshots/models-render.log`, started
anew whenever the palette is opened.

A preset has the `generator` and `settings` of a shape test case (see `tests/e2e/cases`, lengths in mm, angles in
degrees). `"extends": "_bin.json"` takes everything from another preset, so a preset only lists what differs.
`_bin.json` and `_baseplate.json` hold what the dialogs start with, files starting with `_` are only extended.

| Key | |
|---|---|
| `extends` | Another preset file to start from |
| `description` | What the picture shows, not passed on to presets extending this one |
| `generator`, `settings` | What to build, as in a test case |
| `view` | `isoTopRight`, the default, `isoTopLeft`, `isoBottomRight`, `isoBottomLeft`, `front`, `back`, `top`, `bottom`, `left` or `right`. Or `{"eye": [x, y, z], "target": [x, y, z], "up": [0, 0, 1]}` in mm. The bodies are fitted to the picture either way |
| `camera` | `perspective`, the default, or `orthographic` |
| `style` | `shadedWithEdges`, the default, `shaded`, `shadedWithHiddenEdges` or `wireframe` |
| `appearance` | An appearance from Fusion's library by name, such as `Plastic - Glossy (Black)`. A matte plastic without it |
| `color` | `#rrggbb` the appearance is turned into, `#4e79a7` by default, the blue of the dialogs' drawings. `null` keeps the appearance's own color, and Fusion's default look when there's no appearance either |
| `width`, `height` | Picture size in pixels, 2048 by default. The render behind it is `supersample` times larger, at most 6000 pixels |
| `transparent` | `false` for Fusion's background instead of a transparent one |
| `margin` | Space around the model, a share of the picture's width and height, `0.06` by default |
| `supersample` | How many times larger than the picture the render is, `3` by default |
| `exposure`, `saturation` | Stops a viewport picture is brightened by, as a camera's exposure, and how much its colors are deepened, `1` keeps them. `0.85` and `1.4` by default, which bring it close to a ray traced picture of Fusion's. Fusion's viewport has no setting for either, the palette applies them |
| `output` | Folder of the picture, from the add-in folder |
| `difference` | `{"settings": {"hasLipNotches": false}, "color": "#d73a49"}` builds the model again with the settings changed and shows what sets the preset's model apart from it in the color, what it has more and what it lacks, such as the lip notches. Settings changing nothing fail the preset |
| `section` | `{"plane": "xz"}` cuts the model through its middle with a section analysis along `xy`, `xz` or `yz`, the cut faces in the preset's `color`, to show a profile. With `color` `null` Fusion picks the cut's color, it differs between pictures. `"flip": true` keeps the other half |

### From a script

Without the palette, a script in Fusion renders a preset larger than its picture and writes a sidecar of its options
beside it, `commands/commandModelScreenshots/scriptRender.py`:

    from gridkeeper import scriptRender      # while the add-in runs, see api.py
    scriptRender.renderRaw('bin-scoops-4', r'C:\temp\raw')

`tools/screenshots/finishPictures.py` then finishes the renders outside Fusion as the palette's page does (cut to the
model, graded, fitted with the margin, scaled down) and saves each picture where its sidecar says:

    python tools/screenshots/finishPictures.py C:\temp\raw [--only bin-scoops-4]

A model touching the edge of its render is reported, it may be cut off.

### The docs' presets

Every preset is a picture of the docs, and every model picture of the docs has a preset (`tests/test_model_presets.py`).
They extend `_docs.json`, the docs' look: orthographic, the blue `#4A82C8`, shaded, transparent, 1200 × 900 px.
`_bin.json`, `_baseplate.json`, `_label.json`, `_box.json` and `_boxLabel.json` start from what the dialogs start
with; settings a preset leaves out take the dialog's defaults (`lib/defaultSettings.py`), as in a shape test case.
`section` can take an `offset`, mm from the low side of the model instead of its middle, to cut through a magnet socket.

### GIFs

The palette lists the docs' animations of `dev-notes/tools/anim/anims.json` after the presets and screenshots, with the
raw pictures each still misses. **Create**, **Refresh** and **Make GIFs** run `compose.py` for them, which writes
`docs/assets/gif/<name>-light.gif` and `-dark.gif`; its output goes to the log of the pictures.
