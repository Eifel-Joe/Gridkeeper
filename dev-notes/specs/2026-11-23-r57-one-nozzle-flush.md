# Runde 57: Farbabhängige Spülmengen auch für Bambu-Drucker mit einer Düse

Version 1.3.2. Baut auf Runde 56 auf (`2026-11-23-r56-multi-nozzle-flush.md`).

## Problem
Seit 1.3.1 schreibt der Export Spülmengen nach Bambus Farbformel nur für Drucker mit mehr als einem Extruder
(`threeMf.flushSettings`: `extruders < 2` → nichts). Projekte für Drucker mit einer Düse und den H3C haben darum
Bambus Vorgabe: 280 für jeden Farbwechsel, egal welche Farben (Bambu-Test 23.11.2026). Bambu rechnet beim Öffnen
nicht neu (R56-Befund), erst bei Farb-/Filamentwechsel oder „Re-calculate“. Grau→Rot braucht aber z. B. nur ~400,
Schwarz→Weiß deutlich mehr als 280, Blau→Schwarz deutlich weniger.

## Befund (Quelltext Bambu Studio master 8e524a39 = 02.09.01.70)
- Blockzahl der Matrix = Einträge von `flush_multiplier` im Projekt (`PresetBundle::update_multi_material_filament_presets`:
  `old_nozzle_nums = flush_multiplier.size()`, Filamentzahl = √(Matrixlänge / Blockzahl)). Passt das zu
  `get_printer_extruder_count` (= Einträge von `nozzle_diameter`, bei Ein-Düsen-Druckern und H3C 1) und zur
  Filamentzahl, bleibt die Matrix wie geschrieben. Ein Ein-Düsen-Projekt braucht also: `flush_volumes_matrix` mit n²
  Werten und `flush_multiplier` mit **einem** Eintrag (`flush_multiplier_fast` ebenso).
- `flush_volumes_vector` (2n × 140) braucht Bambu nur, wenn die Matrixgröße nicht passt; wir schreiben es wie bei zwei
  Düsen, damit es zur Filamentzahl passt.
- `filament_map`: Bambu setzt beim Start für **jeden** Drucker n × 1 (`PresetBundle.cpp`, `load_selections`:
  `std::vector<int> filament_maps(filament_colors.size(), 1)`), Vorgabe `{1}`. `filament_map_mode`: Vorgabe
  „Auto For Flush“ (`PrintConfig.cpp`). Beides ist bei einer Düse ohne Wirkung, schadet nicht.
- Bambus eigene Ein-Düsen-Projekte enthalten genau diesen Satz:
  `resources/calib/pressure_advance/auto_pa_line_single.3mf` (A1 0.4, 8 Filamente): 64 Matrixwerte,
  `flush_multiplier` `['1']`, `filament_map` 8 × `1`, `filament_map_mode` „Auto For Flush“;
  `auto_pa_line_single_all.3mf` (H2S, 12 Filamente): 144 Werte, ebenso.
- Bambu-Test R56: H3C-Projekt mit einem Block (16 Werte) und denselben Schlüsseln öffnete ohne Warnung.
- Folge: dieselbe Funktion wie bei zwei Düsen, ohne Sonderfall. Keine zusätzlichen Schlüssel.

## Lösung
1. `threeMf.flushSettings` schreibt für **alle** Bambu-Drucker die Spülmengen (Guard `extruders < 2` fällt weg):
   je Extruder ein Block (bei einer Düse und beim H3C einer), Werte nach `flushVolume` mit `nozzleVolumes` und
   `flushDatasets` des Profils. Die 1,3-Regel greift damit nur bei Datensatz ≠ 0, also H2S und H3C, nicht bei
   A1/P1/X1/P2S (Datensatz 0) – wie Bambu.
2. Hinweisfenster (`exportParts.bambuNotice`): der Satz zu Spülmengen und „Re-calculate“ für alle Bambu-Drucker,
   der Satz zur Verteilung auf die Düsen nur bei mehr als einem Extruder:
   „The purging volumes come from Bambu Studio's color formula; for its own filament colors Bambu Studio has its own
   values, Re-calculate under Purging volumes takes them.“ + (nur zwei Düsen) „Bambu Studio puts the filaments on
   the nozzles so it purges least; change that and the volumes there if you want.“
3. Doku: `docs/working/export.md` Abschnitt „Printers with two nozzles“ wird „Purging volumes“ für alle Bambu-Drucker,
   der Teil zur Verteilung auf die Düsen bleibt als eigener Absatz; der H3C-Absatz („Bambu Studio's own purging
   volumes“) wird angepasst. `whats-new.md`, CHANGELOG 1.3.2 (alter 1.3.1-Eintrag bleibt als Geschichte stehen).
4. Version 1.3.2 (Manifest, Manifest-Test).

## Nicht dabei
- Bambus Farbtabellen / gemessene Werte / Long-Retraction-Abzug (Entscheidung R56, Möglichkeit A).
- Andere Drucker als Bambu und *Custom* (Datei je Platte, keine Projekteinstellungen).
- Andere Düsen als 0.4, feste Filament→Düse-Zuordnung, `prime_volume_mode`.

## Ende-zu-Ende-Kriterium
1. pytest grün; `tests/e2e/bambu_project_samples.py` schreibt P1S- und A1-mini-Projekte mit Spülmengen (ein Block).
2. Bambu Studio 02.09.01.70 (Test durch die Hauptsitzung) öffnet die Probedateien aus `_scratch/r57`
   (P1S, A1 mini, H3C, je 4 Farben Grau, Rot, Blau, Schwarz): keine Warnung, alle Platten da, Spülmengen-Dialog zeigt
   die Werte aus der Datei (nicht 280, keine 0 außerhalb der Diagonale), Filamente Bambu PLA Basic ohne Projektkopie,
   eine Platte slict ohne Fehler. „Re-calculate“: Paare mit Grau gleich unseren Werten, Paare aus Rot/Blau/Schwarz
   dürfen abweichen (Bambus Tabelle, bekannt).
3. Fusion-Auftrag `fusion-auftraege/r57_export.py`: Export für einen Ein-Düsen-Bambu-Drucker als Projekt, im
   `project_settings.config` stehen n² Werte, `flush_multiplier` mit einem Eintrag, keine 0 außerhalb der Diagonale.

## Nachtrag Bambu-Test 23.11.2026 (Bambu Studio 02.09.01.70, Probedateien `_scratch/r57`, Stand c45ad1b6)
- P1S, A1 mini, H3C: öffnen ohne Warnung, Spülmengen-Dialog zeigt die Werte der Datei, P1S-Platte slict ohne Fehler.
- H3C: Grau-Paare gleich Bambus „Re-calculate“, nur Paare aus Rot/Blau/Schwarz weichen ab (Farbtabelle, bekannt).
- P1S und A1 mini: „Re-calculate“ ergibt **überall 44 weniger**; der Dialog nennt als Bereich [63, 900] (P1S) bzw.
  [48, 900] (A1 mini) statt nozzle_volume 107 bzw. 92.

### Ursache (Quelltext 8e524a39, `Plater.cpp` `get_min_flush_volumes`)
Die Mindestmenge je Quellfilament ist `int(nozzle_volume)` minus die Länge, die beim Abschneiden zurückgezogen wird
(„Long retraction when cut“), als Filamentvolumen: `π · d²/4 · Länge`, d = `filament_diameter` (1,75), Ergebnis in
`int` abgeschnitten. Die Länge (in `int` abgeschnitten):
- Maschinenwert `retraction_distances_when_cut[Extruder]`, wenn `enable_long_retraction_when_cut` ≠ 0 und
  `long_retractions_when_cut[Extruder]` = 1, sonst 0;
- Filament `filament_long_retractions_when_cut` = 0: 0; = 1 und `enable_long_retraction_when_cut` = 2
  (EnableFilament): `filament_retraction_distances_when_cut` (nil: Maschinenwert); nil (255): bleibt der Maschinenwert.
- Der Abzug gilt nur im Formelweg (`FlushVolCalculator::calc_flush_vol`: Formel, ggf. · 1,3, + Mindestmenge), nicht
  für Werte aus Bambus Farbtabelle.

### Werte (Profile BBL aus 8e524a39, Standard-Variante, Bambu PLA Basic des Druckers)
| Drucker | enable | Maschine an / Länge | Filament an / Länge | Abzug mm | Mindestmenge |
|---|---|---|---|---|---|
| A1 mini, A1, A2L | 2 | 0 / 18 | 1 / 18 | 18 | 92 → 48 |
| P1P, P1S, X1, X1 Carbon | 2 | 0 / 18 | 1 / 18 | 18 | 107 → 63 |
| X1E | 1 | 0 / 18 | 1 / 18 | 0 (Filament zählt nur bei 2) | 107 |
| P2S | 2 | 0 / 18 | nil / 10 | 0 | 110 |
| X2D | 2 | 0, 0 / 18 | nil / 10 | 0 | 92, 92 |
| H2D, H2D Pro | 2 | 0, 0 / 10 | nil / nil | 0 | 130, 145 (wie R56-Test) |
| H2C | 2 | **1, 1 / 14** | nil / nil | 14 | 130 → 96, 145 → 111 (ungeprüft) |
| H2S | 2 | 0 / 18 | nil / nil | 0 | 145 |
| H3C | 2 | 0 / 18 | nil / nil | 0 | 125 (wie Test) |
Gegenprobe: 107 − π·1,75²/4·18 = 63,7 → 63 und 92 → 48,7 → 48, genau Bambus Bereiche; 272 − 44 = 228 wie „Re-calculate“.

### Lösung (Weg A, Formel wie Bambu)
- `BambuProfiles.cutRetractions`: je Extruder die Länge in mm wie oben (aus den Profilen, Fixture
  `machine_extruders[…].cut` mit den Rohwerten; ein Test leitet die Länge nach Bambus Regel daraus ab).
- `threeMf.minFlushVolume(nozzleVolume, cutRetraction)` = `int(int(nozzleVolume) − π·1,75²/4·Länge)`; `flushSettings`
  gibt sie `flushVolume` als Mindestmenge.
- Nicht dabei: andere Filamente als Bambu PLA Basic, vom Nutzer geänderte Rückzugseinstellungen.
- Neue Probedateien P1S und A1 mini; der H2C ändert sich (vorher 130/145) – Vorschlag: H2C-Probe im nächsten
  Bambu-Test mitprüfen.

### Bettanzeige
Die P1S-Probe hat `curr_bed_type` und `bed_type` aller Platten „Textured PEI Plate“ (geprüft). Bambu setzt beim Öffnen
`curr_bed_type` aus dem Projekt (`Plater.cpp`, `load_files` → `on_bed_type_change`); die Auswahl oben links folgt
danach je nach Bambus Einstellung „user_bed_type“ der Liste je Drucker (`Sidebar::update_all_preset_comboboxes`).
Unbestätigt, dass die „Smooth“-Anzeige daher kommt; die Datei selbst ist richtig, keine Änderung.
