# R41 – Dialog-Eingaben: Zahl ohne Einheit formatieren (p291), getippter Spinnerwert beim OK (p490)

Status: abgeschlossen. p490: F mit Doku-Satz. p291: nach Klicktest zurückgenommen, als Fusion-Grenze offen gelassen.

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
   *(nicht erfüllbar, siehe „Ergebnis p291“)*
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
immer.

**Entscheidung: F mit Doku-Satz.** Keine Code-Änderung für p490; Satz in der FAQ (`docs/help/faq.md`, Abschnitt
Building, gilt für alle Dialoge) und eine Zeile im CHANGELOG. Die Auswahlliste aus R37 bleibt.

## Optionen p291

| | Lösung |
|---|---|
| a | in `inputChanged` setzen – gemessen: Anzeige bleibt „2.9“, verworfen |
| b | in `validateInputs` normalisieren – gemessen: Anzeige bleibt „2.9“, verworfen |
| c | per Custom Event nach `inputChanged` normalisieren – gemessen: Anzeige „2.90 mm“ ✔ |

Umgesetzt war c (`lib/ui/expressionFormat.py`: bloße Zahl in der Feldeinheit → `formatInternalValue`, nur wenn der
Wert gleich bleibt; Aufruf aus `CommandUiState.onInputUpdate` und dem Export; dazu setzte `forceUIRefresh` Längen nur
noch bei geändertem Wert, sonst hielt die API schon „1.50 mm“, während das Feld „1.5“ zeigte).

## Ergebnis p291 (Klicktest im Bin-Dialog, Add-in aus dem Worktree, Protokoll im Add-in)

- „1.6“ + Tab → „1.60 mm“; „1.7 mm“ → „1.70 mm“; „1 + 0.5“, „0.05 in“, „1.125“ blieben, wie getippt. Ungültige Werte
  (außerhalb des Bereichs) wurden nicht angefasst.
- **Tippen mit Pause im Feld:** „1.“ getippt, 2 s gewartet → Fusion feuert `inputChanged` schon jetzt, mit dem Ausdruck
  `'1 mm'`; die Formatierung setzte „1.00 mm“ mitten im Tippen, das weitergetippte „55“ ergab „1.00 mm55“ (ungültig).
- Fusion meldet getippten Text nach einer kurzen Tipp-Pause, nicht erst beim Verlassen des Feldes; die API hat kein
  Signal „Eingabe fertig“ oder „Feld hat den Fokus“. Eine Pause ist von Tab nicht zu unterscheiden.
- Weitere Wege: erst formatieren, wenn ein *anderes* Feld geändert wird (sicher, aber „2.9“ bliebe nach Tab stehen,
  bis man woanders etwas ändert); zeitverzögert per Thread (zerstört die Eingabe bei längerer Tipp-Pause genauso).

**Entscheidung: Formatierung weglassen.** p291 ist kosmetisch, gerechnet wird richtig; jede Formatierung nach
`inputChanged` kann eine Eingabe mitten im Tippen zerstören. Der Umbau (Formatierung und `forceUIRefresh`-Änderung) ist
zurückgenommen; p291 bleibt als Fusion-Grenze dokumentiert, keine Code-Änderung.

## Nicht dabei

- Keine Eingabearten umbauen (p490: kein Feldtyp hilft, siehe oben).
- Keine Versionsänderung.

## Ende-zu-Ende-Kriterium

p490: Messung oben (alle Feldarten, OK < 0,3 s nach dem letzten Zeichen) und FAQ-Eintrag „A value I typed was ignored.“
in `docs/help/faq.md`. p291: Klicktest-Befund oben; keine Code-Änderung im Diff.
