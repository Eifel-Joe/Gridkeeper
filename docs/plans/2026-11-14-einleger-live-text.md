# Einleger-Text als Live-Text (p50) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Der Text des Cullenect-Einlegers (Befehl „Gridfinity label“) bleibt echter `SketchText`, je Zeile an einen
Text-User-Parameter gebunden und so nachträglich änderbar. des Nutzers Entscheidung vom 14.11.2026: „Live-Text“.

**Architecture:** Der Label-Builder legt je Textzeile einen Text-Parameter an (`gfLabelN_text1`/`_text2`, wie
`binBuilder.createLabelDefinition`), der Generator bindet jeden `SketchText` per `textParameter.expression` daran,
fixiert Textrahmen und übrige Skizzenpunkte (`_fixSketch`) und extrudiert die `SketchText`-Objekte statt explodierter
Kurven. Der Constraint-Check der Shape-Tests (`commands/commandSnapshotTests/constraints.py`) zählt eine Skizze mit
Live-Text als bestimmt, wenn alle ihre Kurven und Punkte bestimmt oder fixiert sind.

**Spec:** `docs/specs/2026-11-14-cullenect-labels-design.md`, Abschnitt „Vollständig bestimmte Skizzen“.

## Global Constraints

- Nur die Textskizze des Einlegers darf `isFullyConstrained == False` sein, und nur wegen des Textes selbst.
- Symbolskizzen, Grundkörper und Bin-Skizzen unverändert; Bin-Snapshots unverändert.
- Snapshots der vier Label-Fälle nur so weit ändern, wie der Live-Text es erfordert.
- Längen intern in cm.

## Tasks

### Task 1: Constraint-Check erlaubt Live-Text-Skizzen mit sonst bestimmter Geometrie

**Files:** `tests/test_snapshot_constraints.py`, `commands/commandSnapshotTests/constraints.py`

- [x] RED: Skizze mit Text, alle Kurven/Punkte fixiert oder bestimmt ⇒ nicht gelistet; Skizze mit Text und einem
  losen Punkt bzw. einer losen Kurve ⇒ gelistet; Skizze ohne Text, nicht bestimmt ⇒ gelistet.
- [x] GREEN: `unconstrainedSketches` prüft bei Skizzen mit `sketchTexts` die Kurven und Punkte einzeln.

### Task 2: Live-Text im Einleger-Generator

**Files:** `lib/gridfinityUtils/cullenectLabelGenerator.py`, `commands/commandCreateLabel/labelBuilder.py`

- [x] Builder: Text-Parameter je Zeile (`text1`, `text2`), in `LABEL_PARAMETERS` für die Präfixwahl, in die
  Einstellungs-Parameterliste („Text line 1/2“).
- [x] Generator: `CullenectLabelInput.textParameters`; `SketchText` nicht mehr explodieren, an Parameter binden,
  Skizze fixieren, `SketchText`-Objekte extrudieren.
- Nicht automatisiert testbar (Fusion-API). Prüfkriterium: Fusion-Lauf der vier Label-Fälle mit Constraint-Check
  pass; Live-Test unten.

### Task 3: Fusion-Live-Test

- [x] Add-in neu laden, neues Dokument, Einleger 1U mit zwei Zeilen + Schraube erzeugen.
- [x] `gfLabel1_text1` ändern ⇒ Text im Modell geändert, Timeline gesund; Fall „vertieft“ ebenso (Schnitt folgt).
- [x] `gfLabel1_width` ändern ⇒ Symbol bleibt rechts, Text bleibt links.
- [x] Snapshot-Fälle `label_*`: pass bzw. nur durch Live-Text bedingte Änderungen erneuern; Bin-Fälle unverändert.

### Task 4: CHANGELOG-CULLENECT.md

- [x] Satz „fixed curves … generating the insert again“ durch Live-Text-Beschreibung ersetzen.

## Umsetzung, abweichend vom Plan (Befunde im Live-Test)

- Platzierung eines weiteren Einlegers wird in die Skizzen eingerechnet (`cullenectLabelLayout.movedLayout`, Test
  `TestMovedLayout`), statt die Körper zu verschieben: neue Buchstaben blieben sonst am Ursprung.
- Vertiefter/bündiger Text: Schnitt per Extrusion eines deckungsgleichen Zwillingstextes am selben Parameter, statt
  Kombinieren mit den Füllkörpern (verlor Werkzeugkörper bei mehr Buchstaben).
- Snapshots der vier Label-Fälle: nur die Nummerierung der Buchstabenkörper geändert, Fingerabdrücke identisch.
