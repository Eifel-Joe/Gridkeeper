# Components and joints

## Containers

Every new baseplate, bin and insert is a component of its own, in a container of its kind directly in the root of
the design:

| Container | Holds |
|---|---|
| **Grid** | Baseplates |
| **Bins** | Bins |
| **Label** | Cullenect label inserts |
| **Boxes** | Storage boxes, each a component with the components *Box* and *Lid*, the lid jointed shut on the box |

The containers are found by a tag, so you may rename them. They are grounded, so a joint of a part in them moves that
part only, not the container with everything in it. The colored letters of a bin or insert are in a component
**Text** inside it, see [Colors and multicolor printing](colors.md).

![The browser with the container Bins and the component of a 3x2x5 bin in it](../assets/images/browser-components.png)

## Part designs

A part design takes a single component only. When the first model is built in a part design (on **OK**, not for the
preview), Gridkeeper switches it to a hybrid design and says so. Switching keeps the bodies, timeline and parameters,
but a design with components can't go back to a part design.

## Joint origins

A **joint origin** is a small coordinate cross Gridkeeper puts on a model: a point with a direction. Fusion's joints
use them to put one part onto another exactly, and to keep it there when the part below moves or changes size.
Gridkeeper uses joint origins in two ways: some dialogs ask you to *pick* one to say where a new part goes, and
others are there for you to joint parts by hand.

### Where Gridkeeper puts them

| Model | Joint origin | Where | When |
|---|---|---|---|
| Baseplate | *Socket joint origin column-row* | Bottom center of every socket | **Add joint origins** |
| Bin | *Foot joint origin column-row* | Bottom center of every foot | **Add joint origins** |
| Bin with Cullenect pockets | *Pocket joint origin*; with compartments *Compartment 1 pocket joint origin*, *Compartment 2 …* | Middle of every pocket floor, Z up, X along the pocket | always |
| Cullenect insert | *Insert joint origin* | Middle of its bottom | always |
| Storage box | *Cell joint origin column-row* | Floor of every cell | **Add joint origins** |
| Storage box | *Stack bottom joint origin*, *Stack top joint origin* | Middle of the box's underside, middle of the lid's top | always |
| Storage box | *Label joint origin* | In the label holder at the front | always |
| Storage box | *Lid joint origin*, *Latch front left joint origin* and the other seats | Where lid, latches, handle, pins and hinges sit | always, used by the box itself |
| Box label | *Label joint origin* | Middle of the label's back | always |

Column and row count from 1, starting at the front left: *Cell joint origin 1-1* is the front left cell of a box.
All joint origins follow the size parameters of their model.

**Seeing them:** joint origins are listed in the browser under each component, in the folder *Joint Origins*. If you
can't see them in the canvas, open that folder and switch on its light bulb (or the one of the component). Hold the
mouse over a joint origin in the canvas: Fusion shows its name. In a dialog you can also click a joint origin in the
browser instead of the canvas.

### Picking a joint origin in a dialog

Two Gridkeeper dialogs place their part by a joint origin you pick. Only the right kind of joint origin can be picked;
others don't light up.

**A Cullenect insert into a bin's pocket**

1. Build the bin with Cullenect pockets; every pocket gets a pocket joint origin.
2. Open **Gridkeeper label** (the Cullenect insert) and click into **Pocket**.
3. Click the pocket's joint origin in the canvas, or *Pocket joint origin* under the bin in the browser. With
   compartments each pocket has its own: *Compartment 1 pocket joint origin*, *Compartment 2 …* and so on.
4. The size line says whether the insert fits that pocket; an insert wider or higher than the pocket isn't built.
5. **OK**: the insert is jointed into the pocket, flush and centered (joint *… in pocket*).

**The box label into its holder**

1. Open **Gridkeeper box label** and click into **Box**.
2. Click the *Label joint origin* at the front of the box, in the canvas or under the box's component *Box* in the
   browser.
3. **Label width** is set to the box's width (*Box 5 cells*, *Box 6+ cells* …). The width is taken once, when you
   pick: if the box gets wider later, make a new label.
4. **OK**: the label is jointed into the holder (joint *… in holder*).

Without a pick, both dialogs build the part beside the others, unjointed, e.g. for a reprint.

**What happens afterwards**

- *Moving:* a jointed part moves with the part it is jointed to: move the bin, the insert comes along; stack or move
  the box, the label comes along.
- *Rebuild:* inserts in the pockets of a rebuilt bin are jointed into the pockets of the same name again. A rebuilt
  insert has its pocket picked again already. A rebuilt box moves joints on its joint origins over to the joint
  origins of the same name, the label's among them. See [Settings, rebuild and clone](settings-rebuild-clone.md).
- *Clone:* a clone is a new, unjointed part; pick a pocket or a box for it in the dialog.
- *Undoing the joint:* in the browser, open *Joints* (in the root component, at the top of the browser), right-click
  the joint (*… in pocket*, *… in holder*) and **Delete**. The part stays in the design and can be moved or jointed
  anew.

### Jointing by hand

Everything else is jointed with Fusion's **Assemble › Joint** (shortcut **J**). Turn on **Add joint origins** for the
models first.

**A bin into a baseplate or a box cell**

1. **Assemble › Joint**.
2. *Component 1*: click a foot joint origin of the bin, e.g. *Foot joint origin 1-1*.
3. *Component 2*: click the joint origin of the socket it goes into, *Socket joint origin 3-2* of a baseplate or
   *Cell joint origin 3-2* of a box.
4. *Motion*: **Rigid**. **OK**.

Picking the cell in the bin dialog itself comes later (p312).

**A box onto another box**

1. **Assemble › Joint**.
2. *Component 1*: the *Stack bottom joint origin* of the box that goes on top.
3. *Component 2*: the *Stack top joint origin* on the lid of the box below.
4. *Motion*: **Rigid**. **OK**. The upper box sits on the lower one's stacking rim.

A rebuilt bin or baseplate gives only the pocket joints their new joint origins; a joint you made by hand on its foot
or socket joint origins has to be made again. A rebuilt box moves them over by name.

### When it doesn't work

| What you see | Why, and what to do |
|---|---|
| No joint origins in the canvas | Their light bulb is off: open the component's *Joint Origins* folder in the browser and switch it on. For feet, sockets and cells, the model needs **Add joint origins** |
| The joint origin can't be clicked in the dialog | It isn't the kind the dialog takes: **Pocket** takes pocket joint origins only, **Box** only a box's *Label joint origin* |
| The browser shows no joint origins | The folder or the component is collapsed: open the component's arrow, then *Joint Origins* |
| The part sits in the wrong place | Another joint origin was picked, a neighbouring pocket or cell. Hold the mouse over it to see its name; delete the joint and pick again |
| The insert isn't built | It is wider or higher than the pocket, the size line in the dialog says so: pick a pocket that fits or make the insert smaller |

## The active component

After a build the root component is active again, so Fusion doesn't show the other components half transparent.
