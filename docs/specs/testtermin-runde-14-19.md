# Testtermin Runde 14–19

Stand 16.11.2026, Sammelbranch `runde-14-18`. `master` ist unverändert (b367997). Jede Runde ist mit diesen
Prüfungen gemergt:
- pytest grün, zuletzt 910 Tests;
- Ende-zu-Ende-Skripte in Fusion grün;
- 83 von 83 Snapshot-Tests grün;
- Review ohne offene Funde.

Die Belege je Runde stehen in `docs/specs/runde-NN-uebergabe.md`.

## Vorbereitung

1. **Fusion ganz beenden und neu starten.** Der Sammelbranch ist im Fork-Ordner ausgecheckt, Fusion lädt ihn aber erst
   beim Start.
2. **Neues Dokument anlegen** (Datei › Neuer Entwurf). Teste dort, nicht in deinen echten Dokumenten.
3. Die Befehle findest du an zwei Stellen:
   - **Erstellen-Menü** (Konstruktion › Volumenkörper › Erstellen): `Gridfinity bin`, `Gridfinity baseplate`,
     `Gridfinity label`.
   - **Rechtsklick auf einen erzeugten Körper** (im Browser oder im Bild):
     - `Gridfinity settings` öffnet ein Fenster mit den Einstellungen, mit denen der Körper gebaut wurde.
     - `Gridfinity rebuild` öffnet den passenden Dialog mit diesen Werten. Mit OK wird der Körper an seiner Stelle neu
       gebaut.
4. Fusions eigene Menüs sind bei dir deutsch. Das Add-in ist englisch, darum steht jeder Begriff aus dem Add-in unten
   so, wie er im Dialog steht, in `dieser Schrift`.

## Wörterbuch

| Was ich deutsch schreibe | Was im Add-in steht |
|---|---|
| Lasche (für die Beschriftung) | `Label tab` (Gruppe im Bin-Dialog) |
| Beschriftungsart | `Label style`: `Outline`, `Engraved` (graviert), `Embossed` (erhaben), `Cullenect` (Tasche für einen Einleger) |
| Beschriftungstext / fett / Symbol / Farbe | `Label text` / `Bold label text` / `Label icon` / `Label color` |
| Fächer | `Bin compartments`, Knopf `Edit compartment layout` |
| Trennwände bis oben | `Dividers up to the top on grid lines` |
| Wandstärke | `Bin wall thickness` |
| Rastermaß (42 mm) | `Base width unit (mm)` |
| Joint Origins | `Add joint origins` (im Bin- und im Baseplate-Dialog) |
| Einleger | im Dialog `Gridfinity label` als `Insert` angezeigt |
| Breite des Einlegers | Gruppe `Size`: `Width` = `Base units` oder `Width in mm`, dazu `Width (u)` |
| Breiten-/Höhenkorrektur | `Correction width`, `Correction height` (je höchstens ±1 mm) |
| Zeile 1 / Zeile 2 | `Line 1`, `Line 2` (Gruppe `Text`) |
| Schriftart | `Text style`: `Regular`, `Bold`, `Heavy` |
| erhaben / vertieft / bündig | `Text and symbol`: `Raised` / `Set in` / `Flush` |
| Textfarbe | `Text color` |
| Symbol | Gruppe `Symbol`: `Screw` (Schraube aus `Head`, `Shaft`, `Threads`, `Driver`) oder `Hardware` (Mutter, Scheibe, Crimp …) |
| Tasche, in die der Einleger kommt | `Pocket` (im Bild den Joint Origin der Tasche anklicken) |
| Einstellungen speichern / laden | `Save to file` / `Load from file` (im Dialog unter `Inputs` bzw. `Changes`, im Einstellungsfenster als Knopf) |
| Klonen | `Clone into new …` im Einstellungsfenster |
| Vorschau | Gruppe `Preview` |

Fusion selbst: **Ändern › Parameter ändern** ist die Parameterliste. Die Parameter eines Bins beginnen mit `gfBin1_`,
`gfBin2_` …, die eines Einlegers mit `gfLabel1_` …

## Was in den Runden umgesetzt ist

| Runde | Punkte |
|---|---|
| 14 | p72, p120, p71: Wird der Text einer Beschriftung geändert, bleiben die Buchstaben auf der Lasche. Sie sind eingefärbt und haben Namen. |
| 15 | p35: Cullenect erst ab 1,2 mm Wand. p170: Joint Origins folgen dem Raster. p60: Taschen bei Fächern neben dem Raster. p101: Ecken der Trennwände nahtlos bei 2–3 mm Wand. |
| 16 | p30, p34: Snapshot-Tests. p32, p33: Die Einstellungen zeigen die gebaute Laschenbreite und die Taschen. p31: Vorschaubilder. |
| 17 | p110: Unterlängen. p140: Rand bei `Set in`. p52: Luft vor dem Symbol. p51: Symbole schneller (Nylonmutter 23,7 s → 2,9 s). p180: Symbole in Bin-Labels. |
| 18 | p150: Einleger per Rechtsklick neu bauen, Einstellungen speichern, laden und klonen. p151: Label-Farbe bei alten Einstellungsdateien. |
| 19 | p181: Bin-Label-Text beim Verlängern. p210: Umlaute; gemessen, passt, es wurde nichts gebaut. |

Offen ist p53 „Mehrfarbdruck: Text und Symbol sind mehrere Körper“. Dafür ist Handtest 4 da.

---

## Fragen an dich

Bei jeder Frage steht, worum es geht, was heute gebaut ist und was die Wahl bewirkt. Am Ende steht mein Vorschlag. Für
die Antwort reicht „1A, 2A, …“.

### 1. Zwei Zeilen mit vertieftem Text: kleine Kerbe im Rand hinnehmen?

**Worum es geht:** Bei `Text and symbol` = `Set in` wird der Text 0,4 mm tief in den Einleger geschnitten. Außen läuft
ein Rand, der den Einleger in der Tasche hält. Bei zwei Zeilen hat die untere Zeile Buchstaben mit Unterlänge
(g, j, p, q, y). Diese reichen bis 0,22 mm an die Unterkante und schneiden dort eine kleine Kerbe in den Rand. Das
Symbol rechts hält schon 0,4 mm Abstand vom Rand (p140).

**Die Wahl:**
- **A – so lassen.** Kerben gibt es nur unter g, j, p, q, y, sonst ist der Rand ganz. Ob das beim Einrasten stört,
  zeigt ein Probedruck.
- **B – verbieten.** Bei zwei Zeilen mit `Set in` sperrt der Dialog OK und sagt, warum. Dann geht vertieft nur
  einzeilig, oder zweizeilig erhaben bzw. bündig.
- **C – Text hält auch Abstand.** Die Schrift müsste auf 3,27 mm schrumpfen. Regular und Bold sind dann zu dünn zum
  Drucken, zweizeilig vertieft ginge also nur noch in Heavy und auch dort nicht bei −1 mm Höhenkorrektur. Im Ergebnis
  fast wie B, nur umständlicher.

**Mein Vorschlag:** A. Druck einen zweizeiligen Einleger mit `Set in` und „gjpy“ in der unteren Zeile. Rastet er
sauber ein, bleibt es so. Sonst B.

### 2. Warnung bei zu kleiner Schrift: ab welcher Größe?

**Worum es geht:** Ein langer Text wird kleiner gesetzt, damit er passt. Wird er zu klein, druckt eine 0,4-mm-Düse
Teile der Buchstaben nicht. Dann erscheint nach OK der Hinweis „… Below 0.4 mm a 0.4 mm nozzle leaves parts out …“.
Diesen Hinweis gibt es seit Runde 11 (p130). In Runde 17 habe ich die Schriften genauer vermessen. Danach wird Heavy
schon unter **3,05 mm** kritisch, der alte Hinweis kommt aber erst unter **2,79 mm**. Zwischen 2,79 und 3,05 mm baut der
Generator also ohne Warnung eine Schrift, die womöglich Lücken hat.

**Die Wahl:**
- **A – Hinweis an die neue Messung anpassen.** Er kommt bei Heavy dann schon unter 3,05 mm.
- **B – so lassen.**

**Mein Vorschlag:** A, aber erst nach Handtest 15. Zeigt der Slicer bei 3,05 mm noch volle Buchstaben, ist die
Messung zu streng, und dann ist B richtig.

### 3. Einleger ohne Symbol: auch 1 mm Luft am rechten Rand?

**Worum es geht:** Mit Symbol wird der Text so gesetzt, dass vor dem Symbol 1 mm Luft bleibt (p52), auch wenn man den
Einleger mit `Correction width` = −1 mm schmaler macht. Ohne Symbol fehlt diese Luft: Bei −1 mm reicht der Text bis an
den rechten Rand.

**Die Wahl:**
- **A – ja, auch ohne Symbol 1 mm Luft.** Der Text wird dann in solchen Fällen etwas kleiner.
- **B – nein,** der Text darf bis an den Rand.

**Mein Vorschlag:** A, damit es gleichmäßig aussieht.

### 4. Zwei Zeilen in Regular oder Bold bei negativer Höhenkorrektur: sperren?

**Worum es geht:** Mit `Correction height` wird der Einleger niedriger als 11 mm. Bei zwei Zeilen wird die Schrift dann
kleiner, bis die Unterlängen hineinpassen. Regular und Bold dürfen aber nicht kleiner als ihre Druckgrenze werden. Ab
etwa **−0,45 mm** (Regular) bzw. **−0,57 mm** (Bold) passt beides nicht mehr zusammen. Dann zeigt der Dialog
„Two lines don't fit this height …“ und sperrt OK. Bisher wurde trotzdem gebaut, und die Unterlängen standen unten über.

**Die Wahl:**
- **A – sperren, wie jetzt.** Auswege laut Meldung: kleinere Korrektur, eine Zeile oder `Heavy`.
- **B – wieder bauen lassen,** mit überstehenden Unterlängen.

**Mein Vorschlag:** A. Ein Einleger, der unten übersteht, sitzt nicht richtig in der Tasche.

### 5. Zu langer Bin-Label-Text: reicht die Meldung beim OK?

**Worum es geht:** Auf einem Bin-Label (`Label text` im Bin-Dialog) wird ein langer Text kleiner gesetzt, aber nicht
unter die Druckgrenze. Passt er auch dann nicht, wird **nichts gebaut**: Die Vorschau zeigt „failed“, und nach OK
kommt die Meldung „"…" doesn't fit the label even at 3.4 mm … Shorten it or make the bin wider.“ Der Dialog lässt OK
aber vorher anklickbar.

**Die Wahl:**
- **A – so lassen.** Man merkt es an Vorschau und Meldung.
- **B – OK vorher sperren.** Das geht nur mit einer geschätzten Textbreite, denn die echte Breite kennt Fusion erst,
  wenn der Text gebaut ist. Die Schätzung kann daneben liegen: Dann wäre OK bei einem Text gesperrt, der gepasst hätte,
  oder frei bei einem, der nicht passt.

**Mein Vorschlag:** A.

### 6. Text nur über die Parameterliste geändert: Schrift automatisch nachführen?

**Worum es geht:** Du kannst den Label-Text eines Bins in Ändern › Parameter ändern direkt umschreiben. Fusion setzt
dann den neuen Text, aber in der alten Schriftgröße. Ist er länger, läuft er über den Rand, bis du Rechtsklick ›
`Gridfinity rebuild` › OK machst. Der Rebuild passt die Größe an (p181). Fusion selbst kann die Größe nicht nachziehen,
weil seine Formeln die Länge eines Textes nicht kennen; das habe ich in Fusion geprüft.

**Die Wahl:**
- **A – so lassen.** Nach einer Textänderung in der Parameterliste den Bin einmal per `Gridfinity rebuild` neu bauen.
- **B – das Add-in führt die Schrift nach,** sobald du den Parameter-Dialog schließt. Nachteile:
  - Das läuft bei jeder Parameteränderung, auch bei ganz anderen.
  - Es legt einen eigenen Rückgängig-Schritt an.
  - Ohne geladenes Add-in passiert nichts, zum Beispiel wenn jemand anderes die Datei öffnet.

**Mein Vorschlag:** A, außer du änderst Beschriftungen oft über die Parameterliste. Wie machst du das im Alltag?

### 7. Alte Bins mit sehr kleiner Schrift: Neubau ablehnen?

**Worum es geht:** Bins, die vor dieser Version gebaut wurden, können eine Schrift unter der Druckgrenze haben. Damals
kam dafür nur der Hinweis aus Frage 2. Ein `Gridfinity rebuild` lehnt so einen Bin jetzt mit der Meldung aus Frage 5
ab, bis der Text kürzer oder der Bin breiter ist. Reine Parameteränderungen, etwa an der Höhe, gehen weiter.

**Die Wahl:**
- **A – ablehnen, wie jetzt.** Die Schrift wäre beim Druck ohnehin lückenhaft.
- **B – alte Bins mit ihrer alten Schriftgröße neu bauen lassen.**

**Mein Vorschlag:** A.

### 8. Einleger neu bauen: neuer Joint in die Tasche in Ordnung?

**Worum es geht:** Ein Einleger, der in einer Tasche sitzt, ist dort mit einem Joint befestigt. Beim
`Gridfinity rebuild` entsteht der Einleger neu, und mit ihm ein neuer Joint in dieselbe Tasche. Der alte Joint
verschwindet. Hast du selbst etwas auf diesen Joint bezogen, zum Beispiel eine Bewegungsstudie oder einen Kontaktsatz,
geht dieser Bezug verloren. Für das normale Einsetzen ändert sich nichts.

**Die Wahl:**
- **A – in Ordnung.**
- **B – der alte Joint soll erhalten bleiben.** Das wäre aufwändiger und nur nötig, wenn du solche Bezüge benutzt.

**Mein Vorschlag:** A.

Die frühere Frage 9 (Parameternamen wie `gfLabel2_text1`) hast du schon mit „Passt so“ beantwortet.

---

## Handtests

Zu jedem Test steht, **was er prüft**, **was du tust** und **was herauskommen soll**. Geht etwas schief, reicht mir die
Nummer und ein Satz oder ein Bildschirmfoto.

### Bin und Beschriftung

**1. Text verlängern, Buchstaben bleiben auf der Lasche (R14)**
- *Prüft:* Bekommt eine Beschriftung über die Parameterliste mehr Buchstaben, sollen die neuen nicht neben der Lasche
  landen, und sie sollen die Farbe der anderen haben.
- *Tun:*
  1. `Gridfinity bin` mit `Label style` = `Engraved` und einem `Label text`, OK.
  2. Einen zweiten Bin mit `Embossed`, einer `Label color` (z. B. `Red`) und einem anderen `Tab top angle`.
  3. In einem der Bins unter `Edit compartment layout` einem Fach ein eigenes Label geben.
  4. Ändern › Parameter ändern: in jedem Text-Parameter drei Buchstaben anhängen.
- *Erwartet:* Alle Buchstaben liegen auf der Lasche. Beim farbigen Bin sind auch die neuen Buchstaben rot und heißen im
  Browser wie die anderen.

**2. Symbol und Text wandern zusammen (R14)**
- *Prüft:* Ändert sich das Rastermaß, bleiben Symbol und Text gemeinsam auf der Lasche.
- *Tun:*
  1. `Gridfinity bin` mit `Label icon` = `Cullenect nut` (Sechskantmutter) und einem `Label text`.
  2. Den Parameter `gfBinN_baseWidth` von 42 auf 50 mm setzen.
- *Erwartet:* Symbol und Text sitzen weiter nebeneinander auf der Lasche.

**3. Verlängerter Text wird beim Rebuild kleiner (R19, p181)**
- *Prüft:* Nach einer Textänderung in der Parameterliste passt `Gridfinity rebuild` die Schriftgröße an, in jedem Fach.
- *Tun:*
  1. `Gridfinity bin` 2×1 (`Bin width, X (u)` = 2, `Bin length, Y (u)` = 1) mit zwei Fächern (`Bin compartments`).
  2. `Label text` = „Bolzen“, `Bold label text` an, OK.
  3. Ändern › Parameter ändern: den Text-Parameter auf „Bolzen M4x2“ ändern. Er läuft jetzt über den Rand.
  4. Rechtsklick auf den Bin › `Gridfinity rebuild` › OK.
- *Erwartet:* Die Schrift ist kleiner und liegt in beiden Fächern ganz auf dem Label.

**4. Mehrfarbdruck im Slicer (p53, noch offen)**
- *Prüft:* Ein farbiges Label besteht in Fusion aus mehreren Körpern, einem je Buchstabe bzw. Symbol. Die Frage ist, ob
  der Slicer daraus ein Teil oder viele macht.
- *Tun:* Einen Bin mit `Embossed` und `Label color` als 3MF exportieren und in Bambu Studio öffnen.
- *Erwartet:* Am besten erscheinen Bin und Beschriftung als **ein** Objekt mit zwei Teilen, denen du zwei Filamente
  zuweist. Schreib mir, was du siehst: ein Teil, Bin plus ein Beschriftungsteil, oder jeder Buchstabe einzeln.

**5. Symbol bleibt beim Verlängern an seiner Stelle (R17, p180)**
- *Prüft:* Große Cullenect-Symbole auf Bin-Labels wurden beim Textändern verschoben.
- *Tun:* `Gridfinity bin` mit `Label icon` = `Cullenect nut nylon` und langem `Label text`, OK. Dann den Text in der
  Parameterliste verlängern.
- *Erwartet:* Das Symbol bleibt, wo es war.

**6. Cullenect erst ab 1,2 mm Wand (R15, p35)**
- *Prüft:* Unter 1,2 mm Wand ist die Cullenect-Tasche zu schwach. Der Dialog lässt das nicht mehr zu.
- *Tun:* `Gridfinity bin`, `Label style` = `Cullenect`, `Bin wall thickness` = 1,1 mm, dann 1,2 mm.
- *Erwartet:* Bei 1,1 mm ist OK grau, und in der Maßtabelle steht in der Cullenect-Zeile „Cullenect sockets need walls
  of at least 1.2 mm“. Bei 1,2 mm ist OK wieder frei.

**7. Joint Origins folgen dem Rastermaß (R15, p170)**
- *Prüft:* Die Andockpunkte unter den Bin-Füßen und in der Grundplatte wandern mit, wenn das Rastermaß geändert wird.
- *Tun:*
  1. `Gridfinity bin` 4×2 mit `Add joint origins`.
  2. `Gridfinity baseplate` 3×3 mit `Add joint origins`.
  3. Bin und Grundplatte mit einem Joint verbinden (Zusammenfügen › Verbindung).
  4. In der Parameterliste beide Basisbreiten (`…_baseWidth`) auf 50 mm.
- *Erwartet:* Die Joint Origins sitzen wieder in der Mitte der Zellen, der Bin sitzt weiter richtig auf der Platte.

**8. Ecken der Trennwände nahtlos (R15, p101)**
- *Prüft:* Bei dicken Wänden hatten die Rundungen der hochgezogenen Trennwände eine kleine Stufe.
- *Tun:* `Gridfinity bin` 3×2, `Bin wall thickness` = 2 mm, drei Fächer nebeneinander, `Dividers up to the top on grid
  lines` an. Die Ecken oben, wo Trennwand und Außenwand sich treffen, nah heranzoomen.
- *Erwartet:* Die Rundung läuft ohne Stufe durch. Ein schmaler Absatz direkt unter der Stapelkante gehört zur Wand.
- *Hinweis:* Der Dialog erlaubt höchstens 2 mm Wand. 3 mm hat das Testskript geprüft.

**9. Einstellungsfenster zeigt die Cullenect-Maße (R16, p32/p33)**
- *Prüft:* Das Einstellungsfenster zeigt die gebaute Laschenbreite und wie viele Taschen welcher Größe der Bin hat.
  Vorher stand dort „Socket 1: 1U“, als gäbe es nur eine.
- *Tun:* `Gridfinity bin` mit 8 gleichen Fächern und `Cullenect`. Dann Rechtsklick › `Gridfinity settings`.
- *Erwartet:* Im Abschnitt „Cullenect“ stehen `Label tab width … mm (built)` mit mindestens 14 mm und die Zeile
  „1U: 8 sockets, pocket … mm, insert … mm“.

**10. Alte Einstellungsdatei behält die Label-Farbe (R18, p151)**
- *Prüft:* Lädt man eine alte Datei ohne Label-Farbe, sprang die Farbwahl im Dialog auf `None`.
- *Tun:*
  1. `Gridfinity bin`, `Label color` = `Red`.
  2. Unter `Changes` › `Load from file` die Datei
     `docs/specs/testdateien/handtest-10-alte-bin-ohne-farbe.json` aus dem Fork-Ordner laden.
- *Erwartet:* `Label color` steht weiter auf `Red`.

### Einleger

**11. Dialoge öffnen sich nach dem Neustart (R18)**
- *Prüft:* Nach Runde 18 hatte ein Skript-Neuladen die Befehle lahmgelegt. Nach einem echten Neustart müssen sie gehen.
  Das kann nur ein Mensch prüfen.
- *Tun:* Direkt nach dem Neustart `Gridfinity bin`, `Gridfinity baseplate` und `Gridfinity label` je einmal öffnen und
  mit Abbrechen schließen.
- *Erwartet:* Alle drei Dialoge gehen auf.

**12. Unterlängen bei zwei Zeilen (R17, p110)**
- *Prüft:* Bei zwei Zeilen und niedrigerem Einleger dürfen g, j, p, y nicht unten herausragen.
- *Tun:*
  1. `Gridfinity label`, `Width` = `Base units`, `Width (u)` = 1, `Line 1` = „gjpy“, `Line 2` = „Agjp“,
     `Text style` = `Heavy`, `Correction height` = −1 mm, OK.
  2. Dasselbe mit `Text style` = `Regular`.
- *Erwartet:*
  - Bei `Heavy` bleiben die Unterlängen innerhalb des Einlegers.
  - Bei `Regular` zeigt der Dialog „Two lines don't fit this height …“ und OK ist grau (siehe Frage 4).

**13. Rand bleibt bei vertieftem Symbol ganz (R17, p140)**
- *Prüft:* Ein vertieftes Symbol hat den Rastrand angeschnitten.
- *Tun:* `Gridfinity label`, `Width` = `Width in mm`, 25 mm, `Screw` an, `Text and symbol` = `Set in`. Drucken und in
  eine Cullenect-Tasche drücken.
- *Erwartet:* Der Rand ist ringsum ganz, und der Einleger rastet ein.
- *Gleich mitprüfen (Frage 1):* einen zweiten Einleger mit zwei Zeilen, `Set in` und „gjpy“ in `Line 2`.

**14. Nylonmutter in Sekunden (R17, p51)**
- *Prüft:* Einleger mit Hardware-Symbol brauchten über 20 Sekunden.
- *Tun:* `Gridfinity label`, `Hardware` = `Nylon Lock Nut`, OK.
- *Erwartet:* Er ist in wenigen Sekunden fertig, und das Symbol sieht gedruckt aus wie vorher.

**15. Kleinste Schrift im Slicer (R17, Grundlage für Frage 2)**
- *Prüft:* Ob die gemessene Druckgrenze stimmt: Heavy 3,05 mm, Regular 4,43 mm.
- *Tun:*
  1. `Gridfinity label` 1U, `Text style` = `Heavy`.
  2. `Line 1` so lange verlängern, bis nach OK der Hinweis „… mm high, stroke about … Below 0.4 mm …“ kommt. Der
     Hinweis nennt die Höhe.
  3. Einen Einleger knapp darüber und einen knapp darunter als 3MF in Bambu Studio öffnen: 0,4-mm-Düse,
     Standardprofil, Wandgenerator Arachne.
  4. Dasselbe mit `Regular`.
  5. Im Slicer die Vorschau der obersten Schicht ansehen.
- *Erwartet:* Du siehst, ab welcher Größe Teile der Buchstaben fehlen. Für Frage 2 genügt mir: „Heavy bei x mm noch
  ganz“.

**16. Einleger per Rechtsklick neu bauen (R18, p150)**
- *Prüft:* Einleger lassen sich jetzt wie Bins mit geänderten Werten an Ort und Stelle neu bauen.
- *Tun:*
  1. Einen Bin mit `Cullenect` bauen.
  2. `Gridfinity label` bauen und unter `Pocket` den Joint Origin seiner Tasche anklicken.
  3. Rechtsklick auf den Einleger › `Gridfinity rebuild`. Oben im Dialog steht „Rebuilding … in place“.
  4. `Line 1` ändern, OK.
- *Erwartet:* Der neue Einleger sitzt in derselben Tasche, und es gibt nur einen.

**17. Einleger-Einstellungen speichern, laden, klonen (R18, p150)**
- *Tun:*
  1. Rechtsklick auf einen Einleger › `Gridfinity settings` › `Save to file`.
  2. `Gridfinity label` öffnen › unter `Inputs` › `Load from file` › die Datei wählen.
  3. Im Einstellungsfenster `Clone into new …` drücken.
- *Erwartet:* Nach dem Laden stehen im Dialog dieselben Werte. `Clone into new …` öffnet den Label-Dialog mit diesen
  Werten.

**18. Neue Buchstaben gehören zum Einleger (R14, p71)**
- *Prüft:* Nach einer Textänderung hatten neue Buchstaben keinen Namen und wurden nicht als Teil des Einlegers erkannt.
- *Tun:*
  1. Farbigen Einleger bauen (`Text color` z. B. `Red`).
  2. In der Parameterliste den Text (`gfLabel1_text1`) verlängern.
  3. Rechtsklick auf einen der neuen Buchstaben › `Gridfinity settings`.
- *Erwartet:* Das Fenster zeigt die Einstellungen des Einlegers.

**19. Vorschaubild für Snapshot-Tests (R16, p31)**
- *Prüft:* Beim Aktualisieren eines Snapshot-Tests entsteht wieder ein Vorschaubild.
- *Tun:* Dienstprogramme › Add-Ins › `Gridfinity tests: update snapshots`, einen Fall auswählen.
- *Erwartet:* In der Test-Palette erscheint ein Vorschaubild des Falls.

---

## Danach

1. Du schickst mir deine Antworten zu den Fragen (z. B. „1A, 2 nach Test, 3A …“) und die Nummern der Handtests, die
   nicht gepasst haben.
2. Passt alles, mergt die Hauptsitzung auf dein Ja `runde-14-18` nach `master` und setzt die Punkte in der Liste auf
   erledigt.
3. Die Runden-Branches löscht sie nur mit deinem Ja.
4. Was du bei den Fragen anders entscheidest als heute gebaut, wird eine neue Runde.
