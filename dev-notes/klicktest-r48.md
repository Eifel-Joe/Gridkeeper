# Click test round 48: more scoops

Add-in loaded from `wt-r48` (branch `r48-more-scoops`), a new document. Each step: what to do, what must show.

## Bin dialog, Scoop group

1. Open the bin dialog with its defaults. Under **Bin compartments › Scoop**: four checkboxes **Front (along bin
   width)**, **Back (along bin width)**, **Left (along bin length)**, **Right (along bin length)**, all off, and
   **Scoop max radius (mm)** locked.
2. Tick **Left**. The radius unlocks; the preview shows a scoop along the left wall.
3. Tick **Front**, **Back**, **Right** as well (no label tab). Preview: scoops on all four walls, blended at the
   corners, no crack or missing face; OK enabled.
4. Turn on **Add label tab**. **Back** greys out but keeps its tick; the preview drops the back scoop and shows the
   tab. Turn the tab off again: **Back** is enabled and the back scoop is back.
5. With only **Back** ticked and the tab on: the radius locks (no wall has a scoop), OK stays enabled.
6. Bin type **Shelled** or **Solid**: the checkboxes stay as they are, no scoop is built. Custom shape: all four
   and the radius are locked.
7. Hover each checkbox: the tooltip names its wall; **Back** says the label tab sits on the back wall.

## Compartment layout editor

8. Hollow 3x1x4 bin, grid X 3, **Front** ticked in the Scoop group, tab off, **Edit compartment layout** on. The
   drawing marks the front wall of every compartment with a short line.
9. Click the left compartment. The panel shows a row **Scoops**: **Own** off, the four toggles locked and showing
   Front on.
10. Tick **Own**: the toggles unlock, showing the bin's walls. Tick **Left**, untick **Front**. The drawing moves the
    mark to the left wall of that compartment only; the preview follows.
11. Click the middle compartment, tick **Own**, untick everything: no mark, preview without scoops there.
12. Turn the tab on: **Back** in the panel is locked for every compartment.
13. Drag from the left compartment over the middle one to merge them: the merged pocket keeps the left one's walls
    (Left). **Split** it: both cells have Left of their own.
14. **Reset all**: back to single cells, every compartment without Own, marks follow the Scoop group again.

## Saving and rebuild

15. Build a bin from step 10 (own scoops), then rebuild it from its context menu: the dialog opens with the same
    Scoop ticks and the compartment's own walls in the editor.
16. Load a config saved before round 48 with a scoop (e.g. a copy of `dev-notes/specs/testdateien/r32-alte-bin.json`, its
    `hasScoop` set to true): only **Front** is ticked, the bin is built as before.

## Geometry by eye

17. 1x1x6 bin, Front and Back: a strip of flat floor stays between the two scoops (radius limited).
18. 2x1x4 bin, full lip, Left, hollow tab open through the sides: the side opening goes through the left wall.
