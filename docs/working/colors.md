# Colors and multicolor printing

Bin labels and insert texts can be printed in a second filament. Gridkeeper makes the letters and symbols bodies of
their own with a color, so the slicer sees them as separate parts.

## Bin labels

**Label color** in the label tab section: *None*, *Black*, *White*, *Red*, *Orange*, *Yellow*, *Green*, *Blue*,
*Gray* or *Custom* with a `#rrggbb` value in **Custom label color**.

- **None** works as in GridfinityGenerator: raised letters are joined to the bin, engraved and outline ones are cut.
- **A color** keeps the label as bodies of its own: raised letters are not joined to the bin, engraved and outline
  ones fill their cut flush.

## Inserts

**Text color** in the label dialog, with the same choices. Text and symbol of an insert are always bodies of their
own, *Raised*, *Set in* or *Flush*; the color only sets their look.

## In the design

The colored bodies are in a component **Text** inside the bin or insert, so they export together and apart from the
bin. Their appearance is a library plastic recolored and named `Gridfinity label RRGGBB`. It is set on the Text
component, so letters a longer text adds later get the color too. Uncolored bin labels have no bodies of their own
and get no Text component.

![A bin with a red embossed label and its Text component in the browser](../assets/images/colored-label.png)

## Exporting and slicing

Export as **3MF**: every body is an object of its own in its color. In the slicer, assign the label filament to the
text objects of each bin or insert.

!!! note "Known limit"
    A 3MF export lists every letter as an object of its own, not the Text component as one part. Select them together
    in the slicer.

## Printable text

A 0.4 mm nozzle lays lines about 0.42 to 0.45 mm wide. Below the height where the thinnest stroke of a text is one
such line, a slicer leaves parts of the letters out: Regular 4.43 mm, Bold 3.42 mm, Heavy 3.05 mm, measured on the
letters in Fusion. Bin labels are never fitted below it; inserts can be, and a message after building says so. For
small inserts use **Heavy**, its strokes are about 1.5 times as wide as Regular's.
