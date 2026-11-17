# Aufbewahrungsbox nach Pred

Stand 16.11.2026, Jörgs Wunsch: „Als nächstes würde ich gerne Boxen wie diese hier … noch integrieren.“
Vorbild: [Gridfinity Storage Box by Pred (now parametric)](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric),
Fusion-Datei `GridfinityStorageBox_Parametric v1.1.f3d` (letzter Stand, 09.11.2023; eine Pred-Box „v2“ gibt es nicht).

## Warum

Jörg hat Preds Boxen gedruckt und nutzt sie; sie stapeln und verriegeln gut. Gridkeeper soll weitere Boxen in anderen
Größen bauen, die **mit diesen gedruckten Boxen zusammenpassen**: aufeinander stapeln, mit denselben Riegeln verriegeln.
Box und Deckel allein nützen nichts, der ganze Satz mit Zubehör gehört dazu (Jörg: „Box und Deckel ohne das Zubehör
bringt leider nichts.“).

## Ziele

- Neuer Befehl **Gridkeeper box** baut den ganzen Satz einer Box nach Preds v1.1: Box (Unterteil), Deckel, zwei
  Scharniere M3x30, vier Riegel, Griff mit zwei Haltestiften, Schild.
- Maßgleich zu Preds v1.1, damit neue und gedruckte Boxen stapeln und verriegeln.
- Einstellbar: Breite und Tiefe in Rastereinheiten (mindestens 4 × 3), Höhe in Höheneinheiten zu 7 mm (mindestens 5).
- Schild mit Gridkeeper-Text und Cullenect-Symbolen, Aufbau wie unten.
- Alles, was Gridkeeper anlegt, hat vollständig bestimmte Skizzen, auch die Kleinteile.
- Settings, Rebuild und Clone wie bei Bins, Baseplates und Einlegern.

## Nicht-Ziele

- Keine eigene Weiterentwicklung von Preds Form (kein neuer Riegel, kein anderes Scharnier). Passung zu den gedruckten
  Boxen geht vor.
- Nicht die Original-Box (nicht parametrisch) und nicht die Prusa-Mini-Fassung; laut Pred stapeln Original und
  parametrische Box nicht miteinander.
- Kein gedrucktes Scharnier („Hinge“), kein Stift-Scharnier („Hinge_Pined“), kein normaler Riegel („Latch“).
- Nicht die Schubox V2 von schuylab (anderes System, MakerWorld-Standardlizenz, nicht nachbaubar).

## Anti-Ziele

- Eine Box, die gut aussieht, aber auf Jörgs gedruckten Boxen nicht sitzt oder deren Riegel nicht greifen, ist ein
  Fehlschlag, auch wenn alle Tests grün sind.

## Lizenz und Credits

Preds Box steht unter **CC BY-NC** (Printables). Gridkeeper (CC BY-NC-SA) darf sie nachbauen und unter seiner Lizenz
weitergeben: BY-NC verlangt keine gleiche Lizenz. Pflicht: Pred mit Link und Lizenz nennen, Änderungen vermerken, nicht
kommerziell. Credits in CHANGELOG, Release-Text, README, Doku-Seite „Credits“ und im Dialog. Die mitgelieferten
Kleinteil-Dateien tragen einen Herkunftsvermerk.

## Befund aus Preds Datei (16.11.2026, nur gelesen)

- Außenmaß = Rasterzahl × 42 mm + 20 mm (10 mm Rand je Seite); 5 × 4 → 230 × 188 mm.
- Höhe: Unterteil-Extrusion `GridfinityUnit × 7 mm + 10,2 mm`; bei 6 Einheiten Unterteil −2,8 … 44,7 mm, Fuge 42,2 mm,
  Deckel bis 53,7 mm.
- Untere Rille fest 6,2 … 8,2 mm über Unterkante; obere Rille immer 11 mm unter der Fuge; Riegel 36,5 mm lang, endet
  immer 1,55 mm unter Deckeloberkante. **Der Riegel ist bei jeder Höhe dasselbe Teil.**
- Eine Kante der Vorderseite wandert mit 3,5 mm je Einheit (12,2 mm bei 6 Einheiten); bei 5 Einheiten liegt sie bei
  8,7 mm, 0,5 mm über der unteren Rille. Bei 5 Einheiten scheitert in Preds Zeitleiste `Mirror2` (verlorene Kanten),
  bei 6 und 7 nicht.
- Preds Mindestgrößen: X ≥ 4, Y ≥ 3, Höhe ≥ 6.
- Schildbreite `_LabelWidth = min(Grid_X × 42 + 20 − 112 − 47,5; LabelWidth)` mm, `LabelWidth` = 85 mm; Schild
  67,5 × 24,5 mm bei 5 × Y.
- Skizzen der Kleinteile: Riegel (Experimental), Haltestift und leeres Schild vollständig bestimmt. Scharnier M3x30:
  `HingeTabDetails` (4 freie Kurven) und `Sketch3` (6 freie Kurven) nicht. Griff: keine eigene Skizze, seine Extrusion
  hängt an einer Skizze der Box.
- **Druck- statt Einbauposition** (Jörg: „Obacht bei den Scharnieren. Die sind in Druckposition ausgerichtet. Das ist
  nicht die Einbauposition!“): In Preds Datei liegen alle Scharniere neben der Box in Druckposition (Hinge_M3x30 bei
  x −61 … −43 mm, z −12,2 … 19,4 mm, stehend), ebenso `Latch_Experimental` flach am Ursprung (z 0 … 7 mm). Nur der
  normale `Latch` und der Griff sitzen an der Box. Die Einbaulage von Scharnier und Riegel lässt sich also **nicht** aus
  ihrer Lage in Preds Datei übernehmen, sondern muss aus den Aufnahmen der Box abgeleitet werden (Scharnierschlitz:
  `HingeSlotLength`, `HingeSlotFromBack`, `HingeSlotDepth`, `HingeSlotWidth`; Riegel: Lage von `Latch:1`, gleiche
  Skizzen wie `Latch_Experimental`).
- Riegel „Latch_Experimental“: gleiche Skizzen wie „Latch“, dazu ein Rechteckmuster (`R-Pattern2`).

## Wege (Jörg hat B gewählt)

- **A, alles im Code nachbauen:** volle Regeltreue, aber für die Kleinteile rund 130 Schritte mit Rundungen im Code.
- **B, Box/Deckel/Schild im Code, Kleinteile mitgeliefert (gewählt):** Kleinteile sind größenunabhängig; genau Preds
  erprobte Teile, weniger Arbeit.
- **C, Preds Datei als Vorlage parametrieren:** verworfen, übernimmt Mirror2-Fehler, nicht bestimmte Skizze,
  252 Schritte (≈ 50 s je Neuberechnung), passt nicht zu Settings/Rebuild/Clone.

## Entscheidungen (Jörg, 16.11.2026)

- Ganzer Satz, nicht nur Box und Deckel.
- Riegel: **Latch_Experimental**.
- Scharnier: **Hinge_M3x30**.
- Griff wird gebraucht.
- Weg **B**. Ergänzung: Die Kleinteile kommen als Fusion-Bauteile mit Skizzen und Features (keine toten Körper),
  jede Skizze vollständig bestimmt, ohne Benutzerparameter.
- Schild: Gridkeeper-Technik mit Cullenect-Symbolen (Preds Symbolarten sind dort alle enthalten). Aufbau:

  ```
  ┌───────────────────────────────────────┐
  │       │  Zeile 1                      │
  │  M2   │  Zeile 2                      │
  │       ├───────────────────────────────┤
  │       │  Symbole in einer Reihe       │
  └───────────────────────────────────────┘
  ```

  Großes Feld links, zwei Textzeilen rechts, darunter eine Reihe Cullenect-Symbole (so viele die Breite fasst). Text und
  Symbole erhaben, vertieft oder bündig, eigene Farbe, wie bei den Einlegern.
- Mindesthöhe **5** Einheiten (Jörg: „Ist es ein Problem auch 5u zu erzeugen???“ – nein: Preds Mirror2-Fehler kommt aus
  seiner Zeitleiste, Gridkeeper wählt Kanten bei jedem Bau neu; die Körper sind bei 5 gültig).
- Das Schild behält **Preds flaches Plattenprofil** (passt in Preds Halter). Erhabener Text ist erlaubt: Preds eigenes
  `Label_M_Screws` ist 1,25 mm statt 0,85 mm dick, also 0,4 mm erhabene Schrift (Jörg: „Gibt es einen triftigen Grund
  dafür, dass erhabener Text nicht funktionieren sollte?“).
- **Joint origins** (Jörg bei der Freigabe: „Ja, freigegeben. Mit Joint origins.“), wie bei Bins und Baseplates:
  - Option **Add joint origins**: je ein Joint origin unten mittig in jeder Zelle des Box-Bodens, um Bins in die Box zu
    jointen (wie die Sockel der Baseplate, mit dem Raster mitwandernd).
  - An jedem Sitz eines Kleinteils außer den Scharnieren (Riegel, Griff, Haltestift, Schild) ein Joint origin; diese
    Kleinteile werden daran gejointet. Der Deckel wird geschlossen auf die Box gejointet.
- **Scharniere bleiben in Druckposition** (Jörg: „Ich würde die Scharniere in Druckposition belassen.“): Die beiden
  Scharniere M3x30 liegen neben der Box in Preds Druckausrichtung (stehend, beide Hälften verbunden wie in Preds Datei)
  und werden nicht in die Box gejointet.
  - Festlegung der Hauptsitzung: je ein Joint origin mittig auf der Unterseite der Box und oben auf dem Deckel, um Boxen
    aufeinander zu jointen.
- Jörgs gedruckte Boxen sind keine Messreferenz („Ignoriere meine Boxen“); Referenz ist Preds Datei v1.1.

## Festlegungen der Hauptsitzung (nach Builder-Check, von Jörg korrigierbar)

- Preds Werte gelten fest (42 mm Raster, Scharnierspiel 0,15 mm, Schildformel); die Box folgt nicht den globalen
  Gridkeeper-Einstellungen, damit die Passung zu Preds Boxen sicher bleibt.
- Magnetlöcher im Boden (6,5 mm wie Pred) wählbar, Vorgabe aus.
- Großes Feld links: frei eingegebener Text in großer Schrift. Symbolreihe: bis zu fünf Cullenect-Symbole, im Dialog
  gewählt; passt die Breite nicht, entfallen Symbole von rechts, verkleinert wird nichts (bei X = 4 ist das Schild nur
  ≈ 28,5 mm breit).
- Erhabene Schrift Vorgabe 0,4 mm, höchstens so viel, wie der Halter Luft lässt (Builder misst in Preds Halter nach).
  Text und Symbole bleiben im Mittelfeld; der Rand bleibt frei, nach Preds Hinweis 2–3 mm (Builder misst die Lippen).
- Der Satz enthält **4 Riegel** (Jörg: „Je Box werden auch 4 Latches gebraucht.“ und „Latches 2 vorne und 2 jeweils
  einer seitlich hinten“): 2 vorn und an jeder Seite einer, jeweils an der hinteren Seitenaufnahme (`SideCatchTabs`,
  Lage misst der Builder in Preds Datei). Dazu 2 Scharniere M3x30.
- **2 Haltestifte** für den Griff (Jörg: „Handle_Pins werden auch zwei gebraucht. In der Konstruktion ist nur einer.“):
  einer je Griffseite. In Preds Datei steckt nur einer (`HandlePin:1` bei x 58 … 78 mm, links); der zweite sitzt
  gespiegelt an der rechten Griffaufnahme (Lage misst der Builder an `HandleBoltHoles`).
- Eigener Feature-Branch je Runde, Ziel `master` laut Release-Steckbrief (der Sammelbetrieb R14–R19 ist beendet).

## Bauweise (Weg B)

1. **Box und Deckel** baut der Generator im Code wie Bins und Baseplates: vollständig bestimmte Skizzen, Maße aus Preds
   Datei, Benutzerparameter `gfBox1_baseWidth`, `gfBox1_baseLength`, `gfBox1_heightU`. Bodenraster und Bin-Füße im Deckel
   aus den vorhandenen Generatoren (`baseplateGenerator`, `baseGenerator`), soweit maßgleich zu Pred.
   Nachtrag 17.11.2026 (Jörg: „Ja, A bauen“): Die rechten Griff- und Schildhalter baut der Generator selbst als
   Gegenstück der linken (x über die Boxmitte gespiegelt, Fasen- und Rundungskanten ebenso), statt Preds `#42 Mirror6`.
   Fusion konnte diese Feature-Spiegelung je nach Dokumentzustand nicht nachrechnen (`FILLET_NO_EDGE_FOUND`), auch mit
   dem Compute-Typ Identical nicht (`fusion-auftraege/r27_diag2.log`, `r27_cmd.out`). Die Form bleibt Preds, die
   Zeitleiste weicht ab: kein Mirror6, die Features der rechten Hälfte folgen denen der linken.
2. **Kleinteile** (Riegel Experimental, Scharnier M3x30, Griff, Haltestift): einmal aus Preds Datei als eigene
   Fusion-Dateien ins Add-in übernommen, Skizzen dabei nachbestimmt (Scharnier) bzw. neu angelegt (Griff), dann beim Bau
   eingefügt. Keine Benutzerparameter. Riegel, Griff und Haltestift setzen Gelenke in **Einbaulage**, nicht in Preds
   Druckposition (siehe Befund); im Maßvergleich wird die Einbaulage gegen die Aufnahmen der Box geprüft (Riegel auf den
   Haken wie `Latch:1`). Die Scharniere bleiben in Druckposition neben der Box; ihre Passung zum Schlitz prüft der
   Maßvergleich über die Maße (Länge, Tiefe, Breite der Laschen gegen `HingeSlot…`).
   Nachtrag 17.11.2026 (Runde 28, Jörg: „Der Griff bleibt bei Max. 113,5mm stehen. Breiter macht keinen Sinn.“): Der
   Griff ist in Preds Datei kein festes Teil. Er ist so breit wie das Schild plus 28,5 mm (57 / 99 / 113,5 mm bei 4 / 5 /
   ab 6 Einheiten Breite) und hat dort keine eigene Skizze. Abweichung von „feste Teile ohne Parameter“: `handle.f3d`
   bekommt eine eigene, vollständig bestimmte Skizze; ihr einziges Breitenmaß wird beim Einfügen per Ausdruck an die
   Schildbreite der Box + 28,5 mm gebunden (`predBoxSeats.handleWidth`). Eigene Benutzerparameter hat das Teil nicht.
   Nachtrag 17.11.2026 (Runde 28, Jörg: „Am besten doch alle Scharniere mit Auswahl im Generator. Ich hatte zwar das
   Scharnier M3x30 gesagt, aber ich denke alle drei zum auswählen ist besser.“): Der Box-Dialog bekommt eine Auswahl
   **Hinge** mit allen drei Scharnier-Varianten aus Preds Datei, Standard M3x30 wie bisher. Die Wahl steht in den
   Einstellungen der Box (Rebuild und Clone übernehmen sie). Jede Variante kommt wie M3x30 als eigene Datei
   (`resources/predBox`), zwei Stück in Druckposition neben der Box. Ob die Box je Variante eine andere Aussparung braucht,
   klärt `fusion-auftraege/r28_hinge_variants.py`; braucht sie eine, wird das vor dem Bau vorgelegt.
   Lage der Scharniere (Jörg 17.11.2026: „Das passt so für das Scharnier“): das erste dort, wo Preds `Hinge_M3x30:1`
   liegt, das zweite 5 mm daneben in y (`predBoxSeats.HINGE_GAP`), beide in Druckposition; gilt für alle drei Varianten.
   Nachtrag 17.11.2026 (Runde 28, Jörg auf „Scharniere in Druckposition neben der Box festmachen (Vorschlag J), und Lage
   für alle drei so?“: „Ja, beides“): Die Scharniere werden starr gejointet, an zwei Joint origins der Box *Hinge 1 joint
   origin* und *Hinge 2 joint origin* neben der Box in Druckposition, nicht in Einbaulage. So wandern sie mit dem Satz,
   und es gibt kein Positions-Element in der Zeitleiste. Anlass: lose gesetzt blieben sie beim Stapeln liegen, und ihr
   Positions-Element blieb nach dem Rebuild unterdrückt stehen (`fusion-auftraege/r28_cmd.l1.out`, `.l2.out`). Lage je
   Variante: die Ecke ihres Körperquaders (kleinstes x, y, z) dort, wo die von `Hinge_M3x30:1` liegt, das zweite
   Scharnier 5 mm daneben in y, gerechnet von der eigenen Tiefe. Vorgabe M3x30. Damit gilt oben „werden nicht in die
   Box gejointet“ nur noch im Sinn von: nicht in Einbaulage.
   Nachtrag 17.11.2026 (Runde 29, Jörg: „Im Übrigen brauchen Latches, Hinge, Handle und Pin eine andere Farbe als die
   Box und der Deckel.“): Alle Körper der Kleinteile (Riegel, Griff, Haltestifte, Scharnierhälften und der gedruckte
   Stift) bekommen die Darstellung *Gridkeeper box parts*, orange (#F07800) wie der Riegel in Preds Datei (Festlegung
   der Hauptsitzung, Jörg kann sie ändern). Sie wird je Dokument einmal angelegt und wiederverwendet, beim Erzeugen,
   Rebuild und Clone gleich. Box und Deckel bleiben, wie sie sind; die Geometrie ändert sich nicht.
3. **Schild:** gebaut vom Gridkeeper-Schildgenerator (Text, Cullenect-Symbole), Plattengröße nach Preds Formel.
4. Struktur wie bisher: jedes Teil eine Komponente, im Container „Gridkeeper boxes“ o. ä., Gelenke zwischen Teilen.

## Runden (Vorschlag)

1. Box und Deckel im Code, Maßvergleich gegen Preds Datei.
2. Kleinteile übernehmen, nachbestimmen, einfügen, Gelenke.
3. Schild mit Text und Symbolen.

## Ende-zu-Ende-Kriterium

- Je eine Box 5 × 4 × 5 und 5 × 4 × 6 aus Gridkeeper stimmt mit Preds Box 5 × 4 × 6 in allen Außenmaßen, Rillen, Riegelaufnahmen,
  Scharnierschlitzen, Schildhalter und dem Stapelrand auf 0,05 mm überein (Vergleich in Fusion gegen Preds Datei).
- Alle Skizzen des Satzes sind vollständig bestimmt (Snapshot-Test).
- Snapshot-Tests für mehrere Größen und Höhen (5 bis 10), auch nach Parameteränderung; ein Prüfwert sichert den
  Abstand (0,5 mm bei Höhe 5) zwischen wandernder Kante und unterer Rille.
- Probedruck durch Jörg: Deckel schließt, Riegel greifen, zwei Gridkeeper-Boxen stapeln und verriegeln, das Schild
  sitzt im Halter.

## Offen für den Builder

- Wie die Kleinteil-Dateien ins Add-in kommen (f3d einfügen, Format, Ablage) und wie Gelenke sie platzieren.
- Ob Bodenraster und Bin-Füße aus vorhandenen Generatoren maßgleich sind oder Preds Profil nachgebaut werden muss.
- Maße, die nicht in diesem Dokument stehen, misst der Builder in Preds Datei nach (Lage der Riegel und Scharniere,
  Griffhalter, Schildhalter, Luft unter den Lippen).
