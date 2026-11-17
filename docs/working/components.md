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

| Model | Where | When |
|---|---|---|
| Baseplate | Bottom center of every socket | **Add joint origins** |
| Bin | Bottom center of every foot | **Add joint origins** |
| Bin with Cullenect pockets | Middle of every pocket floor, Z up, X along the pocket | always |
| Insert | Middle of its bottom | always |

Joint a bin into a baseplate socket with Fusion's **Joint** command, foot origin to socket origin. Inserts are jointed
into a pocket by the label dialog itself when you pick the pocket, see [Label inserts](../cullenect/inserts.md#pocket).

All joint origins follow the base unit and height parameters of their model.

## The active component

After a build the root component is active again, so Fusion doesn't show the other components half transparent.
