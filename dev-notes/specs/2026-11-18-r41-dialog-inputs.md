# R41 – Dialog-Eingaben: Zahl ohne Einheit formatieren (p291), getippter Spinnerwert beim OK (p490)

Status: Entwurf zur Freigabe; Messung abgeschlossen.

## Problem

- **p291:** Wer in ein Längenfeld eine Zahl ohne Einheit tippt („2.9“), sieht danach „2.9“ statt „2.90 mm“.
  Gerechnet wird richtig. Betrifft alle Längenfelder (Baseplate, Bin, Box, Label, Export).
- **p490:** Bei einem ganzzahligen Spinner (`IntegerSpinnerCommandInput`) meldet Fusion eine getippte Zahl manchmal
  nicht, wenn man direkt aus dem Feld auf OK klickt. Dann gilt der alte Wert. In R37 deshalb für die Export-Filamente
  eine Auswahlliste statt Spinner.

## Bestand

Alle Erzeuger-Dialoge führen ihre Werte in `CommandUiState` (`lib/ui/commandUiState.py`). Der Zustand wird nur in
`inputChanged` über `onInputUpdate` nachgeführt; `execute` liest den Zustand, nicht die Felder. Der Export-Dialog liest
seine Felder beim OK direkt (`layoutOf`).

Fusion-Spinner im Add-in:

| Dialog | Feld | Art | Bereich |
|---|---|---|---|
| Baseplate | Plate width, X (u) / Plate length, Y (u) | IntegerSpinner | 1–100 |
| Box | Width (u) / Length (u) / Height (u) | IntegerSpinner | 4–20 / 3–20 / 6–30 (`addSpinner`) |
| Bin | Bin width, X (u) / Bin length, Y (u) | FloatSpinner, Schritt 0.5 | 0.5–100 |
| Label | Width (u) | FloatSpinner, Schritt 0.5 | 0.5–7 |

Das Raster der Bin-Fächer ist eine HTML-Seite, kein Fusion-Spinner – nicht betroffen.

## Messung (Fusion 2706.1.17, eigener Testdialog mit allen Feldarten, Ereignis-Log je Lauf)

Je Lauf: Feld markieren, Wert tippen, direkt OK (ohne Tab/Enter).

| Lauf | Feld | getippt | inputChanged? | Wert beim OK |
|---|---|---|---|---|
| 1 | IntegerSpinner | 12 | **nein** | (nicht protokolliert, Skriptfehler) |
| 1 | FloatSpinner | 2.5 | ja | 2.5 |
| 1 | ValueInput mm | 2.9 | ja | 2.9 mm |
| 1 | ValueInput ohne Einheit | 4.5 | ja | 4.5 |
| 1 | IntegerSlider (Zahlenfeld tippbar) | 9 | ja | 9 |
| 1 | Textfeld | 7 | ja | '7' |
| 2 | IntegerSpinner | 12 | ja | 12 |
| 3a | IntegerSpinner | 12 | **nein** | 5 (alt) |
| 3b | IntegerSpinner, einziges Feld | 7 | **nein** | 5 (alt) |
| 3c | FloatSpinner | 3.5 | **nein** | 1.0 (alt) |
| 4a | ValueInput ohne Einheit | 4.5 | **nein** | 3.00 (alt) |
| 4b | ValueInput mm | 2.9 | **nein** | 2.50 mm (alt) |
| 4c | IntegerSlider, Zahlenfeld | 9 | **nein** | 5 (alt) |
| 4d | Textfeld | 7 | **nein** | '5' (alt) |

Tippweise: Lauf 1/2 mit ~0,5–1 s zwischen letztem Zeichen und OK-Klick (Bildschirmaufnahme dazwischen); Lauf 3/4
mit OK-Klick < 0,3 s nach dem letzten Zeichen.

**Befund p490:** Es liegt nicht am Spinner. In *jedem* Fusion-Eingabefeld geht eine getippte Eingabe verloren, wenn
OK innerhalb von ~0,3 s nach dem letzten Zeichen geklickt wird: kein `inputChanged`, und das Feld selbst meldet beim
`execute` den alten Wert. Mit ~0,5 s Pause kam der Wert in allen Feldarten an (auch Spinner). Fusion übernimmt
getippten Text offenbar zeitverzögert, nicht beim Fokuswechsel auf OK. Auch der R37-Befund (Klicktest D) entstand mit
sofortigem automatischen Klick.

p291 (Lauf 1/2): Fusion meldet „2.9“ im `inputChanged` als Ausdruck `'2.9 mm'`. Wird in `inputChanged` der Ausdruck
auf `formatInternalValue(value, unitType, True)` = `'2.90 mm'` gesetzt, steht er in der API so (kein zweites
`inputChanged`, keine Schleife), **die Anzeige bleibt aber „2.9“**. `input.value = input.value` ändert den Ausdruck
nicht sofort. Ohne Einheit liefert `formatInternalValue(4.5, '', True)` `'4.5'` (keine Nachkommastellen).
Lauf 3a: in `validateInputs` setzen → API '2.90 mm', Anzeige bleibt „2.9“; per Custom Event nach `inputChanged`
setzen → **Anzeige „2.90 mm“**, kein weiteres `inputChanged`.

## Anforderungen

1. p291: Nach einer getippten Zahl ohne Einheit zeigt ein Längenfeld den Wert normalisiert („2.90 mm“, Format wie beim
   Öffnen des Dialogs). Formeln („10 + 2“, „a*2“) und Werte mit anderer Einheit („1 in“) bleiben, wie getippt. Keine
   Rückkopplung: das Setzen löst keine Endlosschleife aus. Gilt für alle Dialoge mit `CommandUiState` und den Export.
2. p490: siehe Entscheidung unten – kein Feldtyp liefert den Wert bei sofortigem OK.
3. Rechenwerte, gespeicherte Voreinstellungen (`toDict`, Config-Dateien) und Snapshot-Fälle ändern sich nicht.

## Optionen p490

| | Lösung | Bewertung |
|---|---|---|
| A | Beim OK alle Felder direkt lesen | wirkungslos: das Feld meldet selbst den alten Wert (3a/3b/3c/4) |
| B–D | Spinner durch FloatSpinner/ValueInput/Slider ersetzen | wirkungslos: alle verlieren den Wert gleich (3c, 4a–4c) |
| E | Auswahllisten statt Zahlenfelder (wie R37) | wirkt nur für Felder ohne Tippen; für Längenfelder unmöglich, für 1–100 unhandlich |
| F | Keine Code-Änderung; Punkt als Fusion-Verhalten schließen, ggf. ein Satz in der Doku („nach dem Tippen Tab/Enter oder kurz warten“) | ehrlich, keine sichtbare Änderung |

**Empfehlung: F.** Das Add-in kann einen Wert, den Fusion beim OK nicht herausgibt, nicht lesen; jeder Ersatz-Feldtyp
verhält sich gleich. Die Grenze (~0,3 s) erreicht ein Mensch selten (Maus vom Feld zum OK-Knopf), automatische Klicks
immer. Entscheidung über F (inkl. Doku-Satz ja/nein) und ob die R37-Liste so bleibt: Hauptsitzung/User.

## Optionen p291

| | Lösung |
|---|---|
| a | in `inputChanged` setzen – gemessen: Anzeige bleibt „2.9“, verworfen |
| b | in `validateInputs` normalisieren – gemessen: Anzeige bleibt „2.9“, verworfen |
| c | per Custom Event nach `inputChanged` normalisieren – gemessen: Anzeige „2.90 mm“ ✔ |

**Entscheidung: c.** Umsetzung zentral in `lib/ui/expressionFormat.py`:
- reine Funktion `normalizedExpression(expression, unitType, formatted)` → `formatted`, wenn `unitType` eine Längeneinheit
  ist (nicht `''`, nicht `deg`), der Ausdruck eine bloße Zahl mit optional genau dieser Einheit ist und sich vom
  formatierten Text unterscheidet; sonst `None`.
- `start()`/`stop()` registrieren bzw. entfernen ein Custom Event (Muster wie `commandModelScreenshots`), aufgerufen aus
  `commands/__init__.py` neben `selection.start()/stop()`.
- `request(input)` merkt das Feld vor und feuert das Event; der Handler formatiert jedes noch gültige vorgemerkte Feld
  mit `unitsManager.formatInternalValue(value, unitType, True)` und setzt `expression` nur bei Abweichung (keine
  Schleife, gemessen kein Folge-`inputChanged`).
- Aufruf aus `CommandUiState.onInputUpdate` (Zweig `ValueCommandInput`, nicht `deg`) und aus dem `inputChanged` des
  Exports für seine Längenfelder.

## Nicht dabei

- Keine Eingabearten umbauen (p490: kein Feldtyp hilft, siehe oben).
- Winkel- und einheitenlose Felder (`(u)`, `deg`) werden nicht umformatiert – Fusion zeigt dort ohnehin, was getippt
  wurde, und `formatInternalValue` liefert ohne Einheit keine feste Stellenzahl.
- Keine Versionsänderung.

## Ende-zu-Ende-Kriterium

Klicktest im echten Dialog (`dev-notes/klicktest-r41.md`): In Bin, Baseplate, Box, Label und Export ein Längenfeld
„2.9“ + Tab → Feld zeigt „2.90 mm“; „2.9 mm“ ebenso; „10+2“ und „1 in“ bleiben, wie getippt; Winkel- und (u)-Felder
unverändert; erzeugtes Teil wie mit 2.90 mm.
