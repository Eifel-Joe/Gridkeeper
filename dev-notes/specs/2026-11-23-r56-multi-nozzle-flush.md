# Runde 56 (p690): Bambu-Projekt auch für Drucker mit zwei Düsen

Version 1.3.1. Baut auf Runde 55 auf (`2026-11-23-r55-bambu-project-3mf.md`).

## Problem
Seit 1.3.0 schreibt der 3MF-Export für Bambu-Drucker ein Bambu-Studio-Projekt mit allen Platten. Beim H2D meldet
Bambu Studio „Partial purging volume set to 0“. Darum bekommen H2C, H2D, H2D Pro und X2D (`printBeds.TWO_NOZZLES`)
eine Datei je Platte. Ziel: auch sie bekommen das Projekt, ohne Warnung.

## Befund (Quelltext Bambu Studio master 8e524a39, `version.inc` = 02.09.01.70)
- Fehlt `flush_volumes_matrix` im Projekt, nimmt Bambu die Vorgabe aus `PrintConfig.cpp` (4×4, außerhalb der
  Diagonale 280, `flush_multiplier` mit einem Eintrag). `PresetBundle::update_multi_material_filament_presets` baut sie
  für zwei Düsen um und liest dabei für Düse 2 hinter dem Ende der alten Matrix: Nullen oder Zufallswerte. Bambus
  eigenes Beispiel `resources/calib/pressure_advance/auto_pa_line_dual.3mf` (H2D) enthält genau so verschobene Werte
  (`1.04632e-311`). Das ist die Ursache der Warnung.
- `GLCanvas3D::is_flushing_matrix_error` warnt bei Multiplikator 0 oder einer 0 außerhalb der Diagonale, je Block von
  n² Werten (Blockzahl = Einträge von `flush_multiplier`).
- Die Blockzahl ist `get_printer_extruder_count` = Einträge von `nozzle_diameter` des Druckerprofils.
- Bambu rechnet beim Öffnen eines Projekts nicht selbst neu. Neu gerechnet wird erst beim Ändern einer Farbe, eines
  Filaments oder mit „Auto-calc“.
- Bambus Wert je Farbpaar (`FlushVolCalculator::calc_flush_vol`): Farbformel `calc_flush_vol_rgb` (HSV-Abstand und
  Helligkeit, mindestens 60), plus Mindestmenge `nozzle_volume` der Düse (`get_min_flush_volumes`), höchstens 900.
  Bambu kann zusätzlich eine Datentabelle (`FlushVolPredictor`, Datensatz der Düse) und gemessene Werte je
  Filamentpaar nutzen und zieht bei „Long retraction when cut“ ein Stück ab. Unsere Werte sind darum eine
  Näherung an Bambus „Auto-calc“, nicht dieselben Zahlen.

### Bambu-Drucker (0.4-Düse, Profile BBL 02.09.00.74 aus dem Quelltext)
| Drucker | `nozzle_diameter` | `extruder_max_nozzle_count` | `handle_hotend_as_extruder` | `nozzle_volume` Standard je Extruder |
|---|---|---|---|---|
| A1 mini, A1, A2L | 1 | 1 | – | 92 |
| P1P, P1S, X1, X1 Carbon, X1E | 1 | 1 | – | 107 |
| P2S | 1 | 1 | – | 110 |
| H2S | 1 | 1 | – | 145 |
| H2D, H2D Pro | 2 | 1, 1 | – | 130, 145 |
| H2C | 2 | 1, 6 | – | 130, 145 |
| X2D | 2 | 1, 1 | – | 92, 92 |
| H3C | 1 | 9 | 1 | 125.9 |

`nozzle_volume` hat je Extruder mehrere Einträge (Varianten Standard, High Flow, …, `printer_extruder_id` /
`printer_extruder_variant`). Genommen wird die erste Variante des Extruders (`extruder_variant_list`), das ist
Standard, wie `default_nozzle_volume_type`.

## Lösung (vom User freigegeben)
1. Gridkeeper schreibt die Spülmengen selbst in `Metadata/project_settings.config`, als Texte wie Bambu:
   - `flush_volumes_matrix`: je Extruder ein Block von n² Werten (n = Filamente), zeilenweise `von*n+nach`,
     Diagonale 0, Wert = `calc_flush_vol_rgb(von, nach)`, bei Datensatz ≠ 0 (`nozzle_flush_dataset` des Extruders)
     mal 1,3, wenn das Ziel schwarz ist (Bambus Helligkeitsprüfung, siehe Nachtrag), dann + `int(nozzle_volume)` des
     Extruders, höchstens 900.
   - `flush_volumes_vector`: 2n × 140 (Bambus Vorgabe).
   - `flush_multiplier`: je Extruder 1, `flush_multiplier_fast`: je Extruder 1.2.
   - `filament_map`: n × 1 (wie Bambus Beispielprojekt), `filament_map_mode`: „Auto For Flush“.
   Formel nachgebaut mit Quellenangabe (Bambu Studio ist AGPL, kein Code kopiert).
2. Verteilung bleibt „Auto For Flush“: Bambu legt beim Slicen die Farben auf die Düsen. Spülen ja/nein entscheidet
   der Nutzer in Bambu. Das Hinweisfenster vor dem Speichern bekommt einen Satz dazu (nur bei mehr als einer Düse).
3. `TWO_NOZZLES` fällt weg: alle Bambu-Drucker bekommen das Projekt.
4. Düsenzahl aus den Profildaten: `BambuProfiles` bekommt `nozzleVolumes` (je Extruder, Länge = Einträge von
   `nozzle_diameter`), `hotends` (Summe `extruder_max_nozzle_count`) und `hotendAsExtruder`. Die Fixture
   `tests/fixtures/bambu_system_profiles.json` bekommt diese Felder für alle Bambu-Drucker; ein Test vergleicht.
5. Spülmengen schreibt der Export für Drucker mit mehr als einem Extruder. Der H3C bleibt wie 1.3.0 (Nachtrag).

## Frage H3C (vor dem Bambu-Test; entschieden, siehe Nachtrag)
Der H3C hat einen Extruder mit 9 Hotends und `handle_hotend_as_extruder`. Für Bambus Matrix zählt nur
`nozzle_diameter` (1 Eintrag), also ein Block. In 1.3.0 bekommt er das Projekt ohne Spülmengen (ungeprüft).
- Öffnet `r56-h3c-4colours-wie-1.3.0.3mf` ohne Warnung und mit plausiblen Spülmengen (Bambus 280er-Vorgabe): H3C
  bleibt wie Ein-Düsen-Drucker.
- Sonst, und öffnet `r56-h3c-4colours-spuelmengen.3mf` sauber: H3C bekommt Spülmengen mit einem Block.
- Beides nicht: H3C bekommt eine Datei je Platte, neuer Punkt.

## Nicht dabei
- Spülmengen für Ein-Düsen-Drucker (dort sind Bambus Vorgaben gültig, 1.3.0 geprüft).
- Bambus Datentabelle, gemessene Werte je Filamentpaar, Long-Retraction-Abzug, Mehrfarb-Filamente, Stützfilament.
- Feste Zuordnung Filament → Düse; andere Düsen als 0.4; `prime_volume_mode`.

## Ende-zu-Ende-Kriterium
1. Bambu Studio 02.09.01.70 öffnet `r56-h2d-2colours.3mf` und `r56-h2d-4colours.3mf`: alle Platten da, keine
   Meldung „Partial purging volume set to 0“, Spülmengen-Dialog zeigt je Düse die Werte aus der Datei (keine 0
   außerhalb der Diagonale), Filamente Bambu PLA Basic ohne Projektkopie, Slicen einer Platte ohne Fehler.
2. H3C-Dateien wie oben, Ergebnis entscheidet die offene Frage.
3. Nach der Umsetzung: E2E-Skript `tests/e2e/bambu_project_samples.py` schreibt H2D-Projekt mit Spülmengen; pytest grün.

## Nachtrag Bambu-Test 23.11.2026 (Bambu Studio 02.09.01.70, Probedateien aus `_scratch/r56`)
- H2D, 2 Farben: öffnet ohne Warnung, 2 Platten, Spülmengen je Düse wie in der Datei, „Re-calculate“ ergibt dieselben
  Werte. Beide Platten slicen ohne Fehler; Bambu legt Rot und Grau auf verschiedene Düsen.
- H2D, 4 Farben: öffnet ohne Warnung. Bambus „Re-calculate“ weicht bei sieben Paaren ab. Ursache (Quelltext):
  - Bambu sucht zuerst in einer Farbtabelle je Düsentyp (`FlushVolPredictor`, `resources/flush/flush_data_*.txt`,
    19 Bambu-Filamentfarben, je Paar ein Wert). Ähneln beide Farben einer Tabellenfarbe (CIEDE2000 ≤ 5), gilt der
    Tabellenwert ohne `nozzle_volume`. Rot, Blau und Schwarz des Exports treffen sie, Grau nicht.
  - Sonst die Formel; bei Datensatz ≠ 0 mal 1,3, wenn die Quellfarbe „dunkel“ und die Zielfarbe „hell“ heißt. Bambu
    prüft dabei die Helligkeit der 0–255-Werte gegen 180/255 und 75/255: praktisch jede nicht schwarze Quelle und
    nur (fast) schwarze Ziele. Grau→Schwarz: (60 · 1,3) + 130 = 208 statt 190.
  - Gemessene Werte je Filamentpaar (`flush_data_material_pair.json`) gibt es nur für Materialwechsel, nicht für
    PLA Basic zu PLA Basic.
- H3C wie 1.3.0: öffnet ohne Warnung, eine Tabelle mit Bambus Vorgabe 280. H3C mit Spülmengen: öffnet ohne Warnung.

### Entscheidung (User, über die Hauptsitzung, 23.11.2026)
- Möglichkeit A: Farbformel wie Bambu einschließlich der 1,3-Regel, keine Bambu-Tabellen im Code (Daten aus einem
  AGPL-Projekt, von Bambu jederzeit änderbar). Paare zweier Bambu-Standardfarben weichen darum von Bambus
  „Re-calculate“ ab. Das Hinweisfenster sagt, dass Bambu mit „Re-calculate“ im Spülmengen-Dialog genauer rechnet.
- Verworfen: Bambus Tabellen nachbauen (B), je Paar mindestens 280 (C, spült mehr, ohne Schwarz→Rot abzudecken).
- H3C bleibt wie 1.3.0: Projekt ohne Spülmengen.
- Farbabhängige Spülmengen für Drucker mit einer Düse: eigener Punkt p710, nicht in dieser Runde.
