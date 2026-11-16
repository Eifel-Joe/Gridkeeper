# Runde 23 – Übergabe: Umbenennen in Gridkeeper (p234)

Stand 2026-11-16. Branch `runde-23` von `master` (fce1f12), nicht gepusht, nicht gemergt. des Nutzers Entscheidungen
(16.11.): Der Name „Gridkeeper“ ist überall sichtbar, die internen Kennungen bleiben.

## Plan (zur Freigabe)

**Sichtbar wird es Gridkeeper:**
- **Befehlsnamen:** „Gridkeeper bin / baseplate / label / settings / rebuild / clone“, „Gridkeeper tests: run“,
  „Gridkeeper tests: update snapshots“, „Gridkeeper docs: render models“.
  - Die Beschreibungen nennen das Werkzeug nicht; sie bleiben, wie sie sind.
- **Fenster- und Palettentitel:** „Gridkeeper error“, „Gridkeeper tests“, „Gridkeeper model pictures“.
  - Config-Dialoge: „Save/Load Gridkeeper config“, Dateifilter „Gridkeeper config (*.json)“, Meldungstitel „Gridkeeper
    config“.
  - Logs der Tests („Gridkeeper tests panel …“) und der Hinweis „run Gridkeeper tests: update snapshots“.
  - Die Testdokumente heißen „Gridkeeper test …“.
- **Befehls-IDs, Event- und Paletten-IDs:** Sie entstehen aus `config.COMPANY_NAME`/`ADDIN_NAME`. Diese Werte werden
  `EifelJoe`/`Gridkeeper`, also zum Beispiel `EifelJoe_Gridkeeper_cmdBin`. So kollidieren sie nicht mit dem Original,
  das daneben laufen kann.
- **Manifest:**
  - Neue GUID als `id`.
  - `author` „Eifel-Joe“.
  - Beschreibung: „Gridkeeper: Gridfinity bins, baseplates and Cullenect label inserts for Fusion. Based on
    FusionGridfinityGenerator by Le0Michine (CC BY-NC-SA 4.0).“
  - `version` „1.0.0“. Das Format nimmt Fusion als Text; geprüft wird es nach dem Reload in Fusion, ob das Add-in
    startet. Kein Release, kein Tag.
- **`release.yml`:** Das ZIP heißt `Gridkeeper-<tag>.zip`.

**Es bleibt:**
- die Tag-Gruppe der Körper `LevMishin.GridfinityGenerator` und die der Tests `LevMishin.GridfinityGenerator.Tests`;
- die Parameter-Präfixe `gfBin…`, `gfBaseplate…`, `gfLabel…`;
- die Config-Schlüssel und die `generator`-Werte;
- die Namen der erzeugten Körper und Komponenten („Gridfinity bin 2x1x3“, „Gridfinity label 1U …“). Sie beschreiben
  das Gridfinity-Objekt, und Snapshots und Tag-Suche hängen daran.
- die Beschreibungen der Parameter („Gridfinity bin height unit“), aus demselben Grund;
- die Dateien `GridfinityGenerator.manifest` und `GridfinityGenerator.py`. Die benennt die Hauptsitzung zusammen mit
  dem Ordner um.

## Rückfragen (mit Empfehlung)

1. **Ordner im ZIP.** Fusion verlangt, dass Manifest und Ordner gleich heißen. Solange die Dateien
   `GridfinityGenerator.*` heißen, würde ein Ordner `Gridkeeper` im ZIP nicht laden.
   - Empfehlung: In R23 heißt nur das ZIP Gridkeeper. Den Ordner im ZIP stellt die Hauptsitzung zusammen mit der
     Umbenennung der Dateien um, die Zeile dafür steht hier bereit.
2. **Fehlerbericht-Link** (`lib/errorReport.ISSUES_URL`). Er zeigt heute auf die Issues des Originals.
   - Empfehlung: Er zeigt auf die Issues des Forks (`Eifel-Joe/FusionGridfinityGenerator/issues/new`). Berichte über
     Gridkeeper gehören dorthin.
   - Die Wiki-Links zu den Generator-Optionen bleiben beim Original, das regelt die Doku in R24.

## Tests (zuerst)

`tests/test_gridkeeper_names.py`:
- Alle `*CMD_NAME` und Palettentitel beginnen mit „Gridkeeper“.
- Keine Befehls-, Event- oder Paletten-ID beginnt mit `LevMishin_GridfinityGenerator`.
- Tag-Gruppen, Parameter-Präfixe, `generator`-Werte und Körpernamen-Präfixe sind unverändert.
- Manifest: neue GUID, Version 1.0.0, Beschreibung nennt Gridkeeper und Le0Michine.

## Fusion und Klicktests

**Fusion, nur betroffene Fälle:**
- Reload.
- Ein Probe-Auftrag listet die Befehle des Add-ins mit ID und Namen.
- Ein Teil, das vor R23 gebaut wurde, hat dieselbe Tag-Gruppe, `readBodyTag` findet ihn und `canRebuild` ist wahr.
- Snapshot-Lauf: nur ein Bin-, ein Einleger- und ein Grundplatten-Fall. Die Geometrie ändert sich nicht.

**Klicktests:**
- Die Menüs zeigen „Gridkeeper …“.
- Ein alter Bin, vor R23 gebaut, lässt sich per Rechtsklick › „Gridkeeper rebuild“ neu bauen.
- Ein alter Einleger lässt sich per Rechtsklick › „Gridkeeper settings“ öffnen.
