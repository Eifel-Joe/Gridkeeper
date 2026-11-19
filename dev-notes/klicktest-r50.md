# Click test round 50: raised dividers with a pointed top, fixes around scoops

Add-in loaded from `wt-r50` (branch `r50-dividers-lip`), a new document. Each step: what to do, what must show.
Before and after pictures (the reported bin from the same views, a section through two stacked bins, the round 48
cases with two scoop walls, four views of every divider/wall junction) are kept outside the repo with the round's
notes.

## The reported bin

1. Bin dialog with its defaults (2x3x5, hollow, 1.2 mm wall, lip on), **Lip type** Full, **Trim lip top** on.
   Compartments X 2, Y 3, **Dividers up to the top on grid lines** on, **Edit compartment layout** on, every
   compartment **Own** scoops with **Front** only, bin scoops off, no label tab. OK.
2. Look at the dividers in a section across them (Inspect › Section Analysis, plane across the row dividers). Every
   divider goes straight up as thick as below, nothing wider at the top. With **Trim lip top** on its top is flat at
   the lip's trimmed top, about 0.6 mm wide, chamfered at 45 degrees on both sides by about 0.3 mm.
3. The corner where a divider meets the wall, from inside the compartment: one rounding from the compartment's corner
   up over the wall and the lip to the top. Under the full lip it starts where the lip's support leaves the wall and
   runs round the support's end; no flat spot, no sharp corner line.
4. The compartments are as without dividers up to the top: evenly rounded corners, the front row a little shorter only
   by the front scoop wall's inset.
5. Place a second bin of the same size on top (or in the assembly, moved up by 35 mm): its feet sit over the
   dividers, Inspect › Interference finds none.
6. **Trim lip top** off: in the section the divider's top is a roof at 45 degrees, its ridge at the lip's top. A
   stacked bin as in step 5: no interference.

## No gap between a divider and its wall

At every place where a divider meets an outer wall (in the reported bin: the middle divider at the front scoop wall
and at the back wall, both row dividers at the left and right walls) look from four directions: along the wall from
one side, with the camera turned by 90 degrees (along the divider from inside the compartment), from straight above,
and from below inside the compartment up at the junction. The divider runs into the lip without a slot or a notch at
any height, right up to the top of the lip, and the corner beside it is rounded up to the top.

7. The reported bin, at each junction as above.
8. The same bin with each lip variant: Full untrimmed, Light trimmed, Light untrimmed, Full with lip notches. At each
   junction: no gap; the outer faces and the top edge of the wall look as on a bin without dividers to the top,
   nothing sticks out of the wall or over its top.
9. Lip off: **Dividers up to the top** is greyed out, the dividers end below the top as before.

## Other combinations

10. Same bin with the bin scoop **Front** instead of the compartment scoops: as steps 2 to 4.
11. **Dividers up to the top** off, same scoops: as before round 50, compartments evenly spaced, the dividers below the lip.
12. 3x2x3, compartments X 1, Y 2, label style Cullenect, label tab on, dividers up to the top: the tab of the front
    compartment sits at the divider as at a wall, as before round 50; an insert goes into each pocket. The same with a
    light lip.

## Points found on the way (p651 to p653)

13. p651: 2x3x5, Full, compartments 2x3, dividers up to the top, no scoops. Where the dividers cross: their tops
    run into each other, the four compartment corners around the crossing are rounded up to the top, no flat spot.
14. p652: 2x3x1 (one height unit), bin scoop Front. The bin builds (before: an error at the floor fillet); the floor
    beside the scoop is rounded a little.
15. p653: 2x3x5, Full, compartments 1x3, dividers up to the top, bin scoops Front and Left. In the front left corner
    the cavity's corner follows the lip's inner corner up to the top, no flat crescent under the lip. The same in a bin
    without dividers to the top (for example 1x1x3 with four scoops).

## Picture for the docs

16. `docs/assets/images/bin-dividers-to-top.png` is to be taken anew, with the settings of the old picture: a 3x2x3
    bin, compartments X 3 (three side by side), **Dividers up to the top on grid lines** on, everything else at the
    defaults (light lip, trimmed), seen from above at an angle.
