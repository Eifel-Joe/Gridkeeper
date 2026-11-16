# Runde 21 – Übergabe

Stand 2026-11-16. Branch `runde-21` von `master` (c27c32c), nicht gepusht, nicht gemergt.
- Spec: `docs/specs/2026-11-16-runde-21-design.md`.
- Plan: `docs/plans/2026-11-16-runde-21.md`, beide von der Hauptsitzung freigegeben.

Punkte:
- p232 „Hinweis „zu kleine Schrift“ an die gemessene Druckgrenze anpassen“
- p233 „Einleger ohne Symbol: 1 mm Luft am rechten Rand“

## Stand

**p232 (6cc85c9, Review):**
- Der Hinweis folgt nur noch `textStyles.minTextHeight(style)`. Mittlere Strichbreite und `MIN_STROKE` sind entfernt.
- Wortlaut: „"<Text>": <h> mm high, below the <g> mm a 0.4 mm nozzle prints in <Stil>.“ Danach kommt der Rat:
  - Einleger: „Shorten the text, make it wider or use the Heavy style“.
  - Bins: „Make the tab wider“, bei Regular „… or use the Bold style“.
- Die Vorschau-Notiz lautet „, text below the print limit“.
- Beleg: pytest, Grenze je Stil, Heavy 3,0 gegen 3,1 mm, Wortlaut.

**p233 (0ae694f):** `textFitWidth` zieht die 1 mm immer ab, ein- und zweizeilig. Beleg: pytest.

## Review (Opus)

Kein kritischer Fund. Umgang:
- **(I1) behoben:** Ein Bin-Label liegt seit Runde 19 nur auf einer zu niedrigen Lasche unter der Grenze. „Text kürzen
  oder breiter machen“ half dort nicht, jetzt lautet der Rat „Make the tab wider (or use the Bold style)“. Unit-Test.
- **(I2) behoben:** E2E b wäre auch ohne p233 grün gewesen, weil die 5 % Reserve allein 1,7 mm Luft ließ. Jetzt baut b
  denselben Einleger einmal ohne die 1 mm und verlangt, dass die Buchstaben etwa 1 mm weiter links enden.
- **(M1):**
  - Bins haben keinen Heavy-Stil. Das Spec-Kriterium „Bin in Heavy bei 3,0/3,1 mm“ prüft E2E a deshalb mit Regular
    auf einer 6- gegen eine 13-mm-Lasche. Die Grenze Heavy 3,0/3,1 mm prüft der Unit-Test, die Einleger E2E c, mit
    einem Fall ohne Hinweis.
  - Das ist eine Abweichung vom freigegebenen Kriterium und steht auf Jörgs Liste.
- **(M2):** Test-Docstring und CHANGELOG ergänzt. Das Testtermin-Skript `docs/specs/testtermin-runde-14-19.md` zitiert
  noch den alten Wortlaut; es ist historisch und bleibt.
- **(M3):** Zweizeilige Einleger in Regular (3,5 mm) bekommen den Hinweis immer. Das war schon vorher so und ist kein
  Rückschritt.

## Belege

- pytest: `920 passed`.
- Fusion: ausstehend (`r21_reload1`, `r21_e2e_a`–`c`, `r21_snap`).

## Für Jörg

1. Bin-Kriterium mit Regular statt Heavy (siehe M1).
2. Bei Regular und Bold kommt der Hinweis jetzt etwas später als vorher (5,45 → 4,43 und 3,64 → 3,42 mm), bei Heavy
   früher (2,79 → 3,05 mm). Das ist von der Hauptsitzung bestätigt.
