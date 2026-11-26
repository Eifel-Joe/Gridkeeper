# Bekannte Abweichungen von der Gridfinity-Spezifikation { #known-deviations-from-the-gridfinity-specification }

Gridkeeper baut Behälter und Grundplatten nach der Gridfinity-Spezifikation, mit der folgenden bewussten Abweichung
als Vorgabe.

## Stapelrand mit flacher Oberseite { #stacking-lip-with-a-flat-top }

Der Stapelrand am oberen Ende eines Behälters ist **0,6 mm flach** abgeschnitten, statt in einer scharfen Kante
auszulaufen: Seine Oberseite steht **3,8 mm** über der Wand statt 4,4 mm (an einem gebauten Behälter gemessen).

- Wandhöhe, Stapelabstand und der Sitz eines gestapelten Behälters entsprechen der Spezifikation, sodass
  Gridkeeper-Behälter auf und unter anderen Gridfinity-Behältern stapelbar sind.
- Das ist im ursprünglichen GridfinityGenerator absichtlich genauso, siehe
  [Le0Michine/FusionGridfinityGenerator#176](https://github.com/Le0Michine/FusionGridfinityGenerator/issues/176):
  Eine scharfe Kante braucht mehr Filament und druckt nicht sauber, eine flache Oberseite schon.
- Es ist nur die Vorgabe: Ist **Stapelrand oben kürzen** abgeschaltet, bleibt die scharfe Kante erhalten, und
  der **Stapelrandtyp** *Voll* baut das ganze ursprüngliche Profil mit seiner inneren Spitze, siehe
  [Stapelrandtypen](../bins/body.md#lip-types).

![Schnitt durch den Stapelrand an der Ecke eines Behälters: Die Oberseite des Stapelrands ist flach, keine scharfe Kante](../assets/images/lip-flat-top-section.png)
