# Runde 21: Hinweis an der Druckgrenze, Luft ohne Symbol

Stand 16.11.2026. Nutzer: „Starte Runde 21 mit p232 und p233“. Die Entscheidungen sind des Nutzers Antworten am Testtermin.
Branch `runde-21` von `master` (c27c32c).

## Punkte
- p232 „Hinweis „zu kleine Schrift“ an die gemessene Druckgrenze anpassen“
- p233 „Einleger ohne Symbol: 1 mm Luft am rechten Rand“

## p232

**Problem:** Der Hinweis auf zu dünne Schrift (p130) rechnet mit einer geschätzten *mittleren* Strichbreite und einer
Grenze von 0,6 mm (`MIN_STROKE`). Die gemessene Untergrenze aus Runde 17 (`minTextHeight`, dünnster Strich 0,4 mm)
ist eine zweite Zahl. Die beiden passen nicht zusammen:

| Stil | Hinweis heute unter | Druckgrenze (R17) |
|---|---|---|
| Regular | 5,45 mm | 4,43 mm |
| Bold | 3,64 mm | 3,42 mm |
| Heavy | 2,79 mm | 3,05 mm |

**Entscheidung (Nutzer, Testtermin Frage 2):** Der Hinweis kommt ab der Druckgrenze. Er folgt `minTextHeight(style)`,
derselben Quelle wie die Untergrenze; die mittlere Strichbreite und `MIN_STROKE` entfallen. Das gilt überall, wo der
Hinweis entsteht:
- Bin-Dialog: Bin-Label und Fach-Labels;
- Label-Dialog (Einleger);
- die Notiz an der Vorschau-Zeit (`previewNote`);
- alle drei Stile.

**Folge, gewollt:** Bei Heavy kommt der Hinweis früher (ab 3,05 statt 2,79 mm). Bei Regular und Bold kommt er etwas
später (ab 4,43 statt 5,45 bzw. ab 3,42 statt 3,64 mm), weil er jetzt der gemessenen Grenze folgt.

**Wortlaut des Hinweises (Englisch wie die Oberfläche):**
„"<Text>": <h> mm high, below the <g> mm a 0.4 mm nozzle prints in <Stil>.“ Danach kommt der bisherige Rat (kürzen,
breiter machen, Heavy).

## p233

**Problem:** Ein Einleger-Text wird beim Bauen einmal eingepasst. Seit p52 bleibt vor einem Symbol 1 mm mehr Luft,
damit ein später um bis zu 1 mm schmalerer Einleger das Symbol nicht an den Text schiebt. Ohne Symbol fehlt diese Luft:
Bei −1 mm Breite reicht der Text bis an den rechten Rand.

**Entscheidung (Nutzer, Testtermin Frage 3):** Auch ohne Symbol bleibt beim Einpassen 1 mm Luft, ein- und zweizeilig,
bei allen Breiten. Kurzer Text, der ohnehin nicht an den Rand reicht, bleibt unverändert.

## Nicht dabei
- Der Neubau-Ablehnungstext aus Runde 19 (`overflowProblem`): Er nennt die Untergrenze schon heute aus `minTextHeight`.

## Ende-zu-Ende-Kriterium
- **Bin:** Text in Heavy auf 3,0 mm eingepasst (unter 3,05) → `textStyles.notes()` enthält ihn, der Hinweis nennt
  3,05 mm. Bei 3,1 mm gibt es keinen Hinweis.
- **Einleger:** Gleiches für Regular an der Grenze 4,43 mm.
- **Einleger ohne Symbol, langer Text (eingepasst):** Danach Breiten-Parameter −1 mm. Der rechteste Buchstabe bleibt
  ≥ 0 mm vom rechten Rand weg, also innerhalb des Einlegers.
- pytest grün. Snapshot-Tests grün; gewollt geänderte Einleger ohne Symbol werden nur mit belegter Ursache neu
  abgelegt.
