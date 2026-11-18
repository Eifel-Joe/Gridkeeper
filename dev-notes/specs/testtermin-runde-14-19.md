# Testtermin Runde 14–19

**Englische Wörter in fett** = genau so steht es im Add-in. Fusions eigene Menüs stehen deutsch.

## Was du noch selbst machen musst

Am 16.11. wurde schon geprüft:
- Testskripte in Fusion: Tests 1, 2, 3, 5, 7, 8, 9 und 18, alle grün.
- Desktop-Steuerung im echten Dialog: Tests 6, 10, 11, 12, 16, 17 und 19, alle OK. Fotos hast du bekommen.
- Test 16 war zuerst rot und ist in Runde 20 behoben.

Für dich bleiben:
- **Test 4:** farbiges Label im Slicer;
- **Test 13:** Einleger mit vertieftem Symbol drucken und einrasten;
- **Test 14:** Nylonmutter-Einleger drucken;
- **Test 15:** kleinste Schrift im Slicer;
- die **Fragen** unten.

## Vorbereitung

1. Fusion ganz beenden und neu starten. Erst dann lädt Fusion den neuen Stand.
2. Datei › Neuer Entwurf. Teste dort, nicht in deinen echten Dokumenten.
3. Die drei Befehle stehen unter Volumenkörper › Erstellen: **Gridfinity bin**, **Gridfinity baseplate**,
   **Gridfinity label** (das ist der Cullenect-Einleger).
4. Rechtsklick auf einen erzeugten Körper bietet zwei Befehle:
   - **Gridfinity settings** zeigt, womit der Körper gebaut wurde.
   - **Gridfinity rebuild** öffnet den Dialog mit diesen Werten und baut an Ort und Stelle neu.

---

## Handtests

Geht etwas schief: Nummer und ein Satz oder ein Bildschirmfoto an mich.

### Bin und Beschriftung

**1. Text verlängern – Buchstaben bleiben auf der Lasche**
Prüft, dass neue Buchstaben nach einer Textänderung nicht neben der Lasche landen und die Farbe der anderen haben.
1. **Gridfinity bin**: Beschriftungsart **Label style** = **Engraved** (graviert), Text **Label text** = z. B.
   „Schrauben“, OK.
2. Zweiter **Gridfinity bin**:
   - **Label style** = **Embossed** (erhaben);
   - Farbe **Label color** = **Red**;
   - Laschenwinkel **Tab top angle** anders als vorgegeben;
   - OK.
3. Bei einem der beiden Rechtsklick › **Gridfinity rebuild**, dann Fächer bearbeiten (**Edit compartment layout**) und
   einem Fach ein eigenes Label geben, OK.
4. Ändern › Parameter ändern: in jedem Text-Parameter (Name beginnt mit `gfBin`) drei Buchstaben anhängen.

→ Alle Buchstaben liegen auf der Lasche. Beim roten Bin sind auch die neuen Buchstaben rot.

**2. Symbol und Text wandern zusammen**
1. **Gridfinity bin** mit Symbol **Label icon** = **Cullenect nut** (Sechskantmutter) und einem **Label text**, OK.
2. Ändern › Parameter ändern: `gfBin…_baseWidth` (Rastermaß) von 42 auf 50 mm.

→ Symbol und Text sitzen weiter nebeneinander auf der Lasche.

**3. Verlängerter Text wird beim Neubau kleiner**
1. **Gridfinity bin**: Breite **Bin width, X (u)** = 2, Länge **Bin length, Y (u)** = 1, zwei Fächer unter
   **Bin compartments**.
2. **Label text** = „Bolzen“, Fettschrift **Bold label text** an, OK.
3. Ändern › Parameter ändern: Text-Parameter auf „Bolzen M4x2“. Der Text läuft jetzt über den Rand.
4. Rechtsklick auf den Bin › **Gridfinity rebuild** › OK.

→ Die Schrift ist kleiner und liegt in beiden Fächern ganz auf dem Label.

**4. Mehrfarbdruck im Slicer (p53, noch offen)**
1. **Gridfinity bin** mit **Label style** = **Embossed** und **Label color** = **Red**, OK.
2. Als 3MF exportieren und in Bambu Studio öffnen.

→ Schreib mir, was du siehst: ein Teil, Bin plus ein Beschriftungsteil, oder jeder Buchstabe einzeln. Am besten wären
zwei Teile, denen du zwei Filamente gibst.

**5. Großes Symbol bleibt beim Verlängern stehen**
1. **Gridfinity bin** mit **Label icon** = **Cullenect nut nylon** (Nylonmutter) und langem **Label text**, OK.
2. Ändern › Parameter ändern: den Text verlängern.

→ Das Symbol bleibt, wo es war.

**6. Cullenect erst ab 1,2 mm Wand**
1. **Gridfinity bin**, **Label style** = **Cullenect**.
2. Wandstärke **Bin wall thickness** = 1,1 mm.
3. Dann **Bin wall thickness** = 1,2 mm.

→ Bei 1,1 mm ist OK grau, und in der Maßtabelle steht „Cullenect sockets need walls of at least 1.2 mm“.
→ Bei 1,2 mm ist OK wieder frei.

**7. Joint Origins folgen dem Rastermaß**
1. **Gridfinity bin** 4×2 mit Andockpunkten **Add joint origins**, OK.
2. **Gridfinity baseplate** 3×3, ebenfalls mit **Add joint origins**, OK.
3. Bin und Grundplatte mit Zusammenfügen › Verbindung verbinden.
4. Ändern › Parameter ändern: bei Bin und Grundplatte `…_baseWidth` auf 50 mm.

→ Die Andockpunkte sitzen in der Mitte der Zellen, der Bin sitzt weiter richtig auf der Platte.

**8. Ecken der Trennwände nahtlos**
1. **Gridfinity bin** 3×2, **Bin wall thickness** = 2 mm.
2. Drei Fächer nebeneinander.
3. Trennwände bis oben: **Dividers up to the top on grid lines** an, OK.
4. Die Ecken oben heranzoomen, wo Trennwand und Außenwand sich treffen.

→ Die Rundung läuft ohne Stufe durch. Ein schmaler Absatz direkt unter der Stapelkante gehört zur Wand.

**9. Einstellungsfenster zeigt die Taschen richtig**
1. **Gridfinity bin** mit 8 gleichen Fächern und **Label style** = **Cullenect**, OK.
2. Rechtsklick › **Gridfinity settings**.

→ Im Abschnitt „Cullenect“ steht **Label tab width … mm (built)** mit mindestens 14 mm.
→ Darunter steht die Zeile **1U: 8 sockets, pocket … mm, insert … mm**. Früher stand dort „Socket 1: 1U“, als gäbe es
nur eine Tasche.

**10. Alte Einstellungsdatei löscht die Farbe nicht**
1. **Gridfinity bin** öffnen, **Label color** = **Red**.
2. Ganz unten unter **Changes** › **Load from file**.
3. Im Fork-Ordner `docs\specs\testdateien\handtest-10-alte-bin-ohne-farbe.json` wählen.

→ **Label color** steht weiter auf **Red**, nicht auf **None**.

### Einleger

**11. Die Dialoge öffnen sich**
Direkt nach dem Neustart **Gridfinity bin**, **Gridfinity baseplate** und **Gridfinity label** je einmal öffnen und
mit Abbrechen schließen.

→ Alle drei gehen auf.

**12. Unterlängen bei zwei Zeilen**
1. **Gridfinity label**:
   - Breite **Width** = **Base units**, **Width (u)** = 1;
   - Zeilen **Line 1** = „gjpy“, **Line 2** = „Agjp“;
   - Schrift **Text style** = **Heavy**;
   - Höhenkorrektur **Correction height** = −1 mm;
   - OK.
2. Dasselbe mit **Text style** = **Regular**.

→ Bei **Heavy** bleiben g, j, p, y innerhalb des Einlegers.
→ Bei **Regular** meldet der Dialog „Two lines don't fit this height …“ und OK ist grau (siehe Frage 4).

**13. Rand bleibt bei vertieftem Symbol ganz**
1. **Gridfinity label**:
   - **Width** = **Width in mm**, 25 mm;
   - Schraube **Screw** an;
   - Text und Symbol vertieft: **Text and symbol** = **Set in**;
   - OK.
2. Drucken und in eine Cullenect-Tasche drücken.
3. Gleich mit drucken, für Frage 1: zweizeilig, **Set in**, **Line 2** = „gjpy“.

→ Der Rand ist ringsum ganz, und der Einleger rastet ein.

**14. Nylonmutter in Sekunden**
**Gridfinity label**, Symbol **Hardware** = **Nylon Lock Nut**, OK.

→ Fertig in wenigen Sekunden statt über 20. Gedruckt sieht das Symbol aus wie vorher.

**15. Kleinste Schrift im Slicer (Grundlage für Frage 2)**
1. **Gridfinity label** 1U mit **Text style** = **Heavy**.
2. **Line 1** verlängern, bis nach OK der Hinweis „… mm high, stroke about … Below 0.4 mm …“ kommt. Der Hinweis nennt
   die Höhe.
3. Einen Einleger knapp unter und einen knapp über dieser Länge als 3MF in Bambu Studio öffnen: 0,4-mm-Düse,
   Standardprofil, Arachne.
4. In der Vorschau die oberste Schicht ansehen.
5. Dasselbe mit **Text style** = **Regular**.

→ Mir genügt: „Heavy bei x mm noch ganz, bei y mm fehlen Teile“.

**16. Einleger per Rechtsklick neu bauen**
1. **Gridfinity bin** mit **Label style** = **Cullenect**, OK.
2. **Gridfinity label**:
   - unter **Pocket** im Bild den Andockpunkt der Tasche anklicken;
   - OK.
3. Rechtsklick auf den Einleger › **Gridfinity rebuild**. Oben steht „Rebuilding … in place“.
4. **Line 1** ändern, OK.

→ Der neue Einleger sitzt in derselben Tasche, und es gibt nur einen.

**17. Einleger-Einstellungen speichern, laden, klonen**
1. Rechtsklick auf einen Einleger › **Gridfinity settings** › **Save to file**.
2. **Gridfinity label** öffnen › unten unter **Inputs** › **Load from file** › die Datei wählen.
3. Im Einstellungsfenster **Clone into new …** drücken.

→ Nach dem Laden stehen dieselben Werte im Dialog.
→ **Clone into new …** öffnet den Label-Dialog mit diesen Werten.

**18. Neue Buchstaben gehören zum Einleger**
1. **Gridfinity label** mit Textfarbe **Text color** = **Red**, OK.
2. Ändern › Parameter ändern: `gfLabel1_text1` verlängern.
3. Rechtsklick auf einen der neuen Buchstaben › **Gridfinity settings**.

→ Das Fenster zeigt die Einstellungen des Einlegers.

**19. Vorschaubild bei Snapshot-Tests**
1. Dienstprogramme › Add-Ins › **Gridfinity tests: update snapshots**.
2. Einen Fall auswählen.

→ In der Test-Palette erscheint ein Vorschaubild.

---

## Fragen an dich

Antwort kurz, z. B. „1A, 2 nach Test 15, 3A …“.

### 1. Zwei Zeilen vertieft (**Set in**): kleine Kerbe im Rand hinnehmen?

**Worum es geht:** Bei **Set in** wird der Text 0,4 mm tief eingeschnitten. Außen läuft ein Rand, der den Einleger
in der Tasche hält. Bei zwei Zeilen reichen g, j, p, q, y der unteren Zeile bis 0,22 mm an die Unterkante und
schneiden dort eine kleine Kerbe in den Rand. Das Symbol hält schon Abstand.

- **A – so lassen.** Kerben gibt es nur unter g, j, p, q, y. Ob das stört, zeigt Handtest 13.
- **B – verbieten.** Bei zwei Zeilen mit **Set in** ist OK gesperrt. Vertieft geht dann nur einzeilig.
- **C – auch der Text hält Abstand.** Die Schrift müsste dafür so klein werden, dass **Regular** und **Bold** nicht
  mehr druckbar sind. Im Ergebnis fast wie B.

**Vorschlag:** A, wenn der Probedruck aus Handtest 13 sauber einrastet, sonst B.

### 2. Warnung „zu kleine Schrift“: ab welcher Größe?

**Worum es geht:** Lange Texte werden kleiner gesetzt. Zu klein druckt die 0,4-mm-Düse Teile der Buchstaben nicht,
dann kommt der Hinweis „… Below 0.4 mm a 0.4 mm nozzle leaves parts out …“. Nach der neuen Messung wird **Heavy**
schon unter 3,05 mm kritisch, der Hinweis kommt aber erst unter 2,79 mm. Dazwischen wird ohne Warnung gebaut.

- **A – Hinweis schon ab 3,05 mm.**
- **B – so lassen.**

**Vorschlag:** Entscheidung nach Handtest 15. Sind die Buchstaben bei 3,05 mm im Slicer noch ganz, gilt B, sonst A.

### 3. Einleger ohne Symbol: auch 1 mm Luft rechts?

**Worum es geht:** Mit Symbol bleibt vor dem Symbol 1 mm Luft, auch bei **Correction width** = −1 mm. Ohne Symbol
reicht der Text bei −1 mm bis an den rechten Rand.

- **A – auch ohne Symbol 1 mm Luft.** Der Text wird dann etwas kleiner.
- **B – Text darf bis an den Rand.**

**Vorschlag:** A.

### 4. Zwei Zeilen **Regular** oder **Bold** mit negativer **Correction height**: sperren?

**Worum es geht:** Ein niedrigerer Einleger braucht kleinere Schrift, damit die Unterlängen passen. **Regular** und
**Bold** dürfen aber nicht unter ihre Druckgrenze. Ab etwa −0,45 mm (**Regular**) bzw. −0,57 mm (**Bold**) passt
beides nicht mehr. Jetzt sperrt der Dialog OK mit „Two lines don't fit this height …“, siehe Handtest 12. Früher wurde
gebaut, und die Unterlängen standen unten über.

- **A – sperren, wie jetzt.** Ausweg: kleinere Korrektur, eine Zeile oder **Heavy**.
- **B – wieder bauen,** mit überstehenden Unterlängen.

**Vorschlag:** A. Was unten übersteht, sitzt nicht richtig in der Tasche.

### 5. Zu langer **Label text** am Bin: reicht die Meldung beim OK?

**Worum es geht:** Ein zu langer Text wird nur bis zur Druckgrenze verkleinert. Passt er dann immer noch nicht, wird
nichts gebaut. Die Vorschau zeigt „failed“, und nach OK kommt „"…" doesn't fit the label even at 3.4 mm … Shorten it
or make the bin wider.“ OK selbst ist vorher aber anklickbar.

- **A – so lassen.**
- **B – OK vorher sperren.** Das geht nur über eine geschätzte Textbreite, und die kann daneben liegen: Dann wäre OK
  gesperrt, obwohl der Text gepasst hätte, oder frei, obwohl er nicht passt.

**Vorschlag:** A.

### 6. Text nur in der Parameterliste geändert: Schrift automatisch anpassen?

**Worum es geht:** Änderst du den Text in Ändern › Parameter ändern, bleibt die Schriftgröße gleich. Ein längerer
Text läuft dann über den Rand, bis du **Gridfinity rebuild** › OK machst (Handtest 3). Von selbst kann Fusion das nicht
anpassen, weil seine Formeln die Textlänge nicht kennen.

- **A – so lassen.** Nach einer Textänderung einmal **Gridfinity rebuild**.
- **B – das Add-in passt die Schrift beim Schließen der Parameterliste an.** Nachteile:
  - Das läuft bei jeder Parameteränderung, auch bei ganz anderen.
  - Es gibt einen zusätzlichen Rückgängig-Schritt.
  - Ohne geladenes Add-in passiert nichts.

**Vorschlag:** A, außer du änderst Beschriftungen oft über die Parameterliste. Wie machst du das im Alltag?

### 7. Alte Bins mit zu kleiner Schrift: Neubau ablehnen?

**Worum es geht:** Bins von früher können Schrift unter der Druckgrenze haben. Damals gab es nur den Hinweis aus
Frage 2. **Gridfinity rebuild** lehnt solche Bins jetzt ab, mit der Meldung aus Frage 5. Andere Parameteränderungen,
zum Beispiel an der Höhe, gehen weiter.

- **A – ablehnen, wie jetzt.** Gedruckt wäre die Schrift sowieso lückenhaft.
- **B – mit der alten Schriftgröße neu bauen lassen.**

**Vorschlag:** A.

### 8. Einleger neu bauen: neuer Joint in Ordnung?

**Worum es geht:** Ein Einleger in einer Tasche hängt an einem Joint. Bei **Gridfinity rebuild** entsteht ein neuer
Joint in dieselbe Tasche, und der alte verschwindet. Hast du selbst etwas auf den alten Joint bezogen, zum Beispiel
eine Bewegungsstudie, ist dieser Bezug weg. Fürs normale Einsetzen ändert sich nichts.

- **A – in Ordnung.**
- **B – der alte Joint soll bleiben.** Aufwändiger, nur nötig bei solchen Bezügen.

**Vorschlag:** A.

---

## Danach

Schick mir deine Antworten und die Nummern der Handtests, die nicht gepasst haben.
- Passt alles, merge ich auf dein Ja `runde-14-18` nach `master` und hake die Punkte in der Liste ab.
- Was du bei den Fragen anders entscheidest als gebaut, wird eine neue Runde.

<sub>Stand 16.11.2026, Sammelbranch `runde-14-18`. Belege je Runde in `dev-notes/specs/runde-NN-uebergabe.md`.</sub>

## Ergebnis (16.11.2026)

- **Handtests:** alle bestanden. Tests 4, 13, 14 und 15 wurden gedruckt bzw. im Slicer geprüft. Die übrigen liefen per Skript oder per Desktop-Steuerung.
- **Antworten:**
  - **1A:** Kerbe hinnehmen.
  - **2A:** Hinweis ab der Druckgrenze, als p232 neu.
  - **3A:** 1 mm Luft auch ohne Symbol, als p233 neu.
  - **4A:** sperren.
  - **5A:** reicht so.
  - **6A:** nur Rebuild.
  - **7A:** ablehnen.
  - **8A:** neuer Joint in Ordnung.
- **Doku (p230):** vollständig, nur Englisch, im Ordner `docs/` des Forks. Start nach dem Merge nach `master`; vorher wird noch anderes festgelegt.
