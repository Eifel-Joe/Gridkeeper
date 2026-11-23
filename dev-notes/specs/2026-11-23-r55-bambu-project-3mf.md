# Runde 55 (p680): Ein Bambu-Studio-Projekt mit allen Druckplatten

Version 1.3.0. Vorlage: Upstream `1ac1579` (Le0Michine, „Pack the 3MF export on print plates“).

## Problem
Der 3MF-Export schreibt eine Datei je Druckplatte (R29). Ziel: Bambu-Drucker wählen, eine Datei öffnen, alle Platten
sind da, mit unserer Drucklage und den Labelfarben.

## Befund (23.11.2026)
- Bambu Studio übernimmt Platten nur aus einer Datei mit Bambu-Kennung **und** `Metadata/project_settings.config`
  (Quelltext `Plater::priv::load_files`; Plattenprobe R29 vom 17.11.; Test der Hauptsitzung in Bambu Studio
  02.09.01.70, `_scratch/r55-upstream/BEFUND.md`). Ohne Einstellungen schiebt Bambu alle Teile als Ganzes in die
  Bettmitte. Upstreams Datei aus `1ac1579` wird deshalb nicht übernommen.
- Projekt-Einstellungen **nur mit den Profilnamen** öffnen sauber (V2). Bambu ergänzt den Rest aus seinen
  Systemprofilen. Flachgerechnete Profile (V3) sind „Invalid configuration file“.
- In V2 kam Filament 2 als Projektprofil statt als Systemprofil. Ursache nach Quelltext und Systemprofilen: Der P1S hat
  sein eigenes Filamentprofil „Bambu PLA Basic @BBL P1S 0.4 nozzle“, V2 nannte „… @BBL X1C“. Bambu wählt Filament 1
  immer aus, ein weiteres nur, wenn es einem vorhandenen Profil gleicht (`PresetCollection::load_external_preset`,
  `LoadAndSelect::OnlyIfModified`). Festlegung: Je Drucker gilt das Filamentprofil aus `default_filament_profile`
  seines Druckerprofils. Bestätigt wird das erst im Bambu-Test (E2E Punkt 3).
- Nachtrag Bambu-Test 23.11.2026: Der Name war es nicht (Bambus `filament_name_map` setzt ihn ohnehin um). Mit den
  Namen allein kamen Filament 2 und folgende als Projektkopien „(Datei.3mf)“ mit Bambus allgemeinen Vorgaben (Düse
  200 °C, 2 mm³/s), also ein Druckrisiko. Filament-ID, Typ, Hersteller, Düsenvarianten und gleiche Farben änderten
  nichts (Proben A1–A3). Mit `inherits_group` (das Elternprofil je Prozess, Filament und Drucker) nimmt Bambu die
  Systemprofile: alle Filamente „Bambu PLA Basic“ mit 220 °C und 21 mm³/s, Prozess ohne Änderungsstern (Probe B1).
  Außerdem führt Bambu den Betttyp je Platte; ohne `bed_type` in den Plattendaten kam beim P1S Smooth PEI.

## Entscheidungen (vom User, über die Hauptsitzung)
1. Die Datei gibt sich als Bambu Studio aus: `Application` = `BambuStudio-02.09.01.70`, `BambuStudio:3mfVersion` = 1.
2. Nur 0,4-mm-Düse. Je Bambu-Drucker eine kleine Namenstabelle im Code: Druckerprofil, Prozessprofil
   „0.20mm Standard @BBL …“, Filamentprofil. Keine Profilinhalte, nichts vom Rechner des Users lesen.
3. Jeder Filament-Slot bekommt „Bambu PLA Basic“ in der Variante des Druckers, mit den Farben aus dem Export.
4. Druckbett: Textured PEI (`curr_bed_type` = `Textured PEI Plate`).
5. Nur Bambu-Drucker. Für andere Drucker und Custom bleibt alles wie heute: eine Datei je Platte.
6. Vor dem Speichern des Projekts kommt ein Hinweisfenster mit Bestätigung (Text siehe unten). Abbrechen schreibt nichts.

## Anforderungen
1. **Druckerliste** wandert nach `lib/printBeds.py` (wie Upstream), geteilt von Baseplate- und Export-Dialog.
   Die Bambu-Sammeleinträge werden aufgeteilt, damit jede Zeile genau einem Druckerprofil entspricht:

   | Eintrag (Bett in mm) | Druckerprofil | Prozessprofil | Filamentprofil |
   |---|---|---|---|
   | Bambu Lab A1 mini (180 x 180) | Bambu Lab A1 mini 0.4 nozzle | 0.20mm Standard @BBL A1M | Bambu PLA Basic @BBL A1M |
   | Bambu Lab A1 (256 x 256) | Bambu Lab A1 0.4 nozzle | 0.20mm Standard @BBL A1 | Bambu PLA Basic @BBL A1 |
   | Bambu Lab A2L (330 x 320) | Bambu Lab A2L 0.4 nozzle | 0.20mm Standard @BBL A2L | Bambu PLA Basic @BBL A2L 0.4 nozzle |
   | Bambu Lab P1P (256 x 256) | Bambu Lab P1P 0.4 nozzle | 0.20mm Standard @BBL P1P | Bambu PLA Basic @BBL P1P |
   | Bambu Lab P1S (256 x 256) | Bambu Lab P1S 0.4 nozzle | 0.20mm Standard @BBL X1C | Bambu PLA Basic @BBL P1S 0.4 nozzle |
   | Bambu Lab X1 (256 x 256) | Bambu Lab X1 0.4 nozzle | 0.20mm Standard @BBL X1C | Bambu PLA Basic @BBL X1 |
   | Bambu Lab X1 Carbon (256 x 256) | Bambu Lab X1 Carbon 0.4 nozzle | 0.20mm Standard @BBL X1C | Bambu PLA Basic @BBL X1C |
   | Bambu Lab X1E (256 x 256) | Bambu Lab X1E 0.4 nozzle | 0.20mm Standard @BBL X1C | Bambu PLA Basic @BBL X1C |
   | Bambu Lab P2S (256 x 256) | Bambu Lab P2S 0.4 nozzle | 0.20mm Standard @BBL P2S | Bambu PLA Basic @BBL P2S |
   | Bambu Lab X2D (256 x 256) | Bambu Lab X2D 0.4 nozzle | 0.20mm Standard @BBL X2D | Bambu PLA Basic @BBL X2D 0.4 nozzle |
   | Bambu Lab H2C (330 x 320) | Bambu Lab H2C 0.4 nozzle | 0.20mm Standard @BBL H2C | Bambu PLA Basic @BBL H2C |
   | Bambu Lab H2D (350 x 320) | Bambu Lab H2D 0.4 nozzle | 0.20mm Standard @BBL H2D | Bambu PLA Basic @BBL H2D |
   | Bambu Lab H2D Pro (350 x 320) | Bambu Lab H2D Pro 0.4 nozzle | 0.20mm Standard @BBL H2DP | Bambu PLA Basic @BBL H2DP |
   | Bambu Lab H2S (340 x 320) | Bambu Lab H2S 0.4 nozzle | 0.20mm Standard @BBL H2S | Bambu PLA Basic @BBL H2S |
   | Bambu Lab H3C (330 x 320) | Bambu Lab H3C 0.4 nozzle | 0.20mm Standard @BBL H3C | Bambu PLA Basic @BBL H3C |

   Herkunft: `default_print_profile` und `default_filament_profile` der Druckerprofile von Bambu Studio
   02.09.01.70 (beim Entwickeln gelesen, nicht zur Laufzeit). Ein Test prüft die Tabelle gegen eine eingecheckte
   Liste der Systemprofilnamen. Die Spülturm-Ecken und Sperrflächen bleiben je Drucker wie bisher. Die Sperrfläche
   gilt für P1P, P1S, X1, X1 Carbon und X1E. Die alten Sammeleinträge (`P1P, P1S, X1, X1C, X1E`, `P2S, X2D`,
   `H2D, H2D Pro`) öffnen als X1 Carbon, P2S und H2D (`OLD_BED_NAMES`), mit derselben Bettgröße. Die anderen
   Drucker bleiben wie sie sind.
1a. **Zuletzt gewählter Drucker als Vorgabe** (Freigabe 23.11.2026: „Vorgabe soll der zu letzt ausgewählte Drucker
   sein.“). Beide Dialoge teilen sich die Wahl. Mit OK schreiben sie den Eintrag des Drucker-Dropdowns, auch
   „Custom“, in `commandConfig/lastPrinter.txt` im Add-in-Ordner (`printBeds.readLastPrinter`/`writeLastPrinter`).
   - **Export-Dialog:** Er öffnet mit diesem Drucker, alte Sammeleinträge abgebildet wie oben. Bei „Custom“ gilt die
     im Export gespeicherte Größe. Fehlt die Datei, gilt der bisher im Export gespeicherte Drucker. Ist auch der nicht
     da, gilt „Bambu Lab X1 Carbon (256 x 256 mm)“, bisher der Sammeleintrag mit X1C.
   - **Baseplate-Dialog:** Er öffnet mit diesem Drucker und dessen Bettgröße. Bei „Custom“ bleibt seine eigene
     Größe. Fehlt die Datei, bleibt es wie heute: gespeicherte Vorgaben, sonst Custom. Eine Baseplate, die neu gebaut
     oder aus einer Konfiguration geladen wird, behält das Bett ihrer Konfiguration. Beim Neubau oder Klon zählt ihr
     Bett nur dann als gewählter Drucker, wenn Drucker oder Bettgröße beim OK anders sind als beim Öffnen
     (Review R55). Alte Sammeleinträge in den gespeicherten Vorgaben werden wie oben abgebildet.
   - Ein unbekannter Eintrag in der Datei zählt wie keine Datei.
2. **Dialog:** Ist ein Bambu-Drucker gewählt und das Format 3MF, erscheint die Auswahl „Files“:
   „One Bambu Studio project with all plates“ (Vorgabe) oder „A file per plate“. Für andere Drucker und Custom gibt
   es die Auswahl nicht, dort gilt immer eine Datei je Platte. Die Wahl wird mit den anderen Export-Einstellungen
   gespeichert. Namen wie Upstream: `FILES_ONE`, `FILES_PER_PLATE`.
3. **Projektdatei** `<Name>.3mf`, auch bei nur einer Platte. Dann gibt es Profile, Farben und Bett ebenso.
   - **Drucklage, Verteilen, Platten:** wie heute aus `printLayout.layOutKinds`. Box-Teile, Scharnier, Labels und
     Platten nach Art bleiben, Teile gruppiert, Spülturm-Ecke und Sperrfläche frei.
   - Jede Platte rückt in Bambus Plattengitter, `plateOrigin`/`plateColumns`/`PLATE_GAP` wie Upstream
     (`lib/threeMf.py`). Die Teile bleiben dabei wie heute in der Plattenmitte; Bambu verschiebt in einer
     Projektdatei nichts mehr.
   - Aufbau wie V2: Jedes Objekt liegt um seinen Mittelpunkt, die Lage steht in `transform` des `build`-Items.
     `Metadata/model_settings.config` (`modelSettings`, `MODEL_SETTINGS_PATH` wie Upstream) nennt Objektname,
     Extruder 1, Teil mit Einheitsmatrix und je Platte ihre Objekte.
   - Die Labelfarben stehen wie heute als `paint_color` an den Dreiecken.
   - `Metadata/project_settings.config` enthält nur: `version`, `name`, `from`, `printer_settings_id`,
     `print_settings_id`, `filament_settings_id` (je Slot das Filamentprofil des Druckers), `filament_colour`,
     `curr_bed_type` und `inherits_group` = [Prozess, Filament 1…n, Drucker] mit denselben Namen (Nachtrag
     23.11.2026). Jede Platte trägt `bed_type` = Textured PEI Plate.
   - **Filament-Slots:** so viele wie die höchste vergebene Filamentnummer, mindestens 1. Slot 1 ist der Körper,
     Farbe `#808080` (grau, wie V2). Ein Labelslot bekommt die Farbe seines Labels. Text ohne Farbe bekommt
     `#000000`. Lücken zwischen vergebenen Nummern werden mit `#808080` gefüllt.
   - Ist „Color label text“ aus, gibt es nur Slot 1.
4. **Eine Datei je Platte** (andere Drucker, oder bei Bambu gewählt): unverändert wie R29.
5. **Hinweis vor dem Speichern** des Projekts (Fusion-`messageBox`, Knöpfe OK/Cancel; Fusion kann die Knöpfe nicht
   umbenennen). Erst nach der Rückfrage zum Ersetzen vorhandener Dateien, Cancel schreibt und löscht nichts.
   Text (Englisch wie die ganze Oberfläche):

   > This file is a Bambu Studio project with all 3 plates. It comes with Bambu Studio's standard profiles:
   > Bambu Lab P1S 0.4 nozzle, 0.20mm Standard @BBL X1C, Bambu PLA Basic for every filament and the Textured PEI
   > Plate. Change them in Bambu Studio to your printer, nozzle, filament and plate where they differ.
   >
   > OK saves the project, Cancel saves nothing.

   Plattenzahl, Drucker- und Prozessname sind die der Wahl. Bei einer Platte heißt es „with its plate“.
   Gridkeeper öffnet die Datei nicht selbst in Bambu Studio. Darum kommt der Hinweis nur vor dem Speichern.
6. **Meldung danach** wie heute, dazu „Bambu Studio project with N plates“.

## Optionen und Entscheidung
- **Upstreams `bedPacking` statt `printLayout`:** verworfen für diese Runde. `printLayout` hat Drucklage, Gruppen,
  Platten nach Art und die Prüfung von Spülturm und Sperrfläche. `bedPacking` kennt davon nichts. Ein Ersatz würde
  die Box-Sätze und Labels umwerfen. Was `bedPacking` dichter packt, prüft p13.
- **Upstreams Datei ohne Einstellungen:** verworfen, Bambu übernimmt die Platten nicht (Befund).
- **Vorlage-Projekt vom User:** verworfen (Entscheidung 2, nichts vom Rechner lesen).
- Übernommen von Upstream, mit gleichen Namen und Dateien: `lib/printBeds.py`, `PURGE_ANCHORS`, `EXCLUDED_AREAS`,
  `plateColumns`, `plateOrigin`, `PLATE_GAP`, `MODEL_SETTINGS_PATH`, `modelSettings`, `FILES_ONE`,
  `FILES_PER_PLATE`. Das erleichtert die Übernahme in p13. Upstreams Kommentar „They read it from a plain 3MF too“
  wird nicht übernommen.

## Nicht dabei
- OrcaSlicer, PrusaSlicer und andere Drucker (bleiben bei einer Datei je Platte); Düsen außer 0,4 mm.
- Profilinhalte, Profile vom Rechner des Users, Prozess- oder Filamentwahl im Dialog.
- Zwei-Düsen-Zuordnung (H2C, H2D, H2D Pro, X2D): Bambu verteilt die Filamente selbst. Öffnet eines davon im Test nicht
  sauber, fällt es auf „A file per plate“ zurück und kommt auf die Liste.
- Vorschaubilder der Platten und `slice_info.config`; Öffnen in Bambu Studio aus Fusion heraus.
- Ältere Bambu-Studio-Versionen: Ist die eigene Version älter als 02.09, zeigt Bambu evtl. „newer version“, lädt aber.
  Geprüft wird nur 02.09.01.70.

## Ende-zu-Ende
1. pytest grün; die Profiltabelle stimmt mit den eingecheckten Systemprofilnamen überein.
2. Beispieldatei aus den Unit-Test-Daten unter `D:\Entwicklung\Gridfinity\_scratch\r55`. Sie hat drei Platten mit
   Bins und Labels, Labeltext in zwei Farben und ohne Farbe, für P1S. Dazu je eine Ein-Platten-Datei für A1 mini und
   H2D.
3. In Bambu Studio 02.09.01.70 (Hauptsitzung): Die Datei öffnet ohne „Invalid configuration“. Alle Platten sind richtig
   belegt, die Teile liegen auf ihren Platten. Druckerprofil, „0.20mm Standard“ und alle Filamente sind Systemprofile
   „Bambu PLA Basic“ ohne Projektprofil. Die Farben stimmen, die Labelbuchstaben sind gefärbt. Das Bett ist Textured
   PEI, der Spülturm steht frei.
4. Fusion-Lauf (Hauptsitzung): Export eines Box-Satzes und eines Mixes für einen Bambu-Drucker, einmal als Projekt
   und einmal je Platte, ohne Fehler; Hinweisfenster erscheint, Cancel schreibt nichts.
