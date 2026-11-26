# German glossary

For `lib/i18n/de.json` and the German docs pages (`docs/**/*.de.md`). Words Fusion has are taken from Fusion's own
German interface (`tools/i18n/fusionTerms.py` looks them up in the local Fusion install); Gridfinity's own words
were decided with the spec `dev-notes/specs/2026-11-26-r60-german.md`.

## Style

- Address the user formally with *Sie*, as Fusion's German interface does ("Möchten Sie …?", "Wählen Sie … aus.").
- Input names are short, about 24 characters at most (Fusion cuts longer ones off), the tooltip explains: "Wandstärke",
  "Höhe, Z (u)", "Ø Schraubenbohrung"; checkboxes name the feature, a verb only where it says what happens
  ("Stapelrand erzeugen", "Magnetaussparungen"). German dialogs are 150 px wider than English ones (lib/ui/dialogSize.py).
- Units and symbols stay: mm, u, °, ×. Numbers in texts get a decimal comma (`i18n.number`), a space before mm in
  running text ("83,5 mm").
- Keep product and format names: Gridkeeper, Gridfinity, Cullenect, Fusion, 3MF, STL, STEP, Bambu Studio, OrcaSlicer,
  PrusaSlicer, GitHub.
- Keep the {placeholders} exactly; HTML tags and links in a text stay as they are.
- Name Fusion's commands and dialogs as German Fusion does (table below), in the same marks as the English text.

## Fusion's words

| English | German |
|---|---|
| Scripts and Add-Ins / Add-Ins / Utilities | Skripte und Zusatzmodule / Zusatzmodule / Dienstprogramme |
| Solid (tab) / Create / Modify | Volumenkörper / Erstellen / Ändern |
| Change Parameters / User Parameters / Model Parameters | Parameter ändern / Benutzerparameter / Modellparameter |
| Browser / Timeline / Text Commands | Browser / Zeitachse / Textbefehle |
| Component(s) / Body (Bodies) / Sketch / Occurrence | Komponente(n) / Körper / Skizze / Exemplar |
| Joint / Joint Origin(s) / Rigid Group | Gelenk / Gelenkursprung (Gelenkursprünge) / Starre Gruppe |
| Part Design / Hybrid Design / Capture Design History | Bauteilkonstruktion / Hybride Konstruktion / Konstruktionsverlauf erfassen |
| Appearance / Material | Darstellung / Material |
| Fillet / Chamfer / Shell / Extrude / Combine / Pattern | Abrundung / Fase / Schale / Extrusion / Kombinieren / Anordnung |
| Feature(s) (in the timeline) | Element(e) |
| Export / Mesh / Save / Open / Insert | Exportieren / Netz / Speichern / Öffnen / Einfügen |
| OK / Cancel / Preview / Apply / Close / Reset | OK / Abbrechen / Vorschau / Anwenden / Schließen / Zurücksetzen |
| Settings / Preferences / General / Options / Advanced / Custom | Einstellungen / Voreinstellungen / Allgemein / Optionen / Erweitert / Benutzerdefiniert |
| Default(s) / Restore defaults | Vorgabe(n) / Vorgaben wiederherstellen |
| Width / Length / Height / Depth / Thickness / Diameter / Radius / Offset | Breite / Länge / Höhe / Tiefe / Dicke / Durchmesser / Radius / Versatz |
| Distance / Spacing / Tolerance / Size / Position / Placement | Abstand / Abstand / Toleranz / Größe / Position / Platzierung |
| Grid / Origin / Center / Snap / Units / inch / Millimeters | Raster / Ursprung / Mitte / Fang / Einheiten / Zoll / Millimeter |
| Top / Bottom / Front / Back / Left / Right | Oben / Unten / Vorne / Hinten / Links / Rechts |
| Face(s) / Edge(s) / Profile / Floor / Hole(s) / Counterbore | Fläche(n) / Kante(n) / Profil / Boden / Bohrung(en) / Zylindrische Senkung |
| Font / Bold / Italic / Text / Color | Schriftart / Fett / Kursiv / Text / Farbe |
| Select / Selection / Edit / Show / Hide / Visible | Auswählen / Auswahl / Bearbeiten / Anzeigen / Ausblenden / Sichtbar |
| Yes / No / Error / Warning / Info / Help / Details | Ja / Nein / Fehler / Warnung / Informationen / Hilfe / Details |
| Check for updates / Update / Download / Install / Restart / Version | Nach Updates suchen / Aktualisieren / Herunterladen / Installieren / Neu starten / Version |
| Copy / Folder / File name / Overwrite / Replace / Format / Printer | Kopieren / Ordner / Dateiname / Überschreiben / Ersetzen / Format / Drucker |
| Fully constrained (sketch) | vollständig bestimmt |

## Gridfinity and Gridkeeper words

| English | German |
|---|---|
| bin | Behälter |
| baseplate | Grundplatte |
| base (of a bin, its feet) | Füße |
| base unit / height unit (u) | Rastereinheit / Höheneinheit (u) |
| half grid | Halbraster |
| xy clearance | Spiel XY |
| stacking lip / lip / lip notches / lip type | Stapelrand / Stapelrand / Kerben im Stapelrand / Stapelrandtyp |
| label tab | Beschriftungslasche |
| scoop | Griffmulde |
| compartment / divider / compartment layout | Fach / Trennwand / Fachaufteilung |
| hollow / shelled / solid (bin type) | Hohl / Schale / Voll |
| magnet cutout / magnet hole / screw hole | Magnetaussparung / Magnetloch / Schraubenbohrung |
| fold walls, creases | Wände falzen, Falze |
| custom shape (of a bin) | Eigene Form |
| Cullenect label insert / insert / pocket / socket | Cullenect-Einleger / Einleger / Aufnahme / Steckplatz |
| label (text on a part) | Beschriftung |
| symbol | Symbol |
| storage box / box / lid / hinge / latch / handle | Aufbewahrungsbox / Box / Deckel / Scharnier / Verschluss / Griff |
| small parts (of a box) | Kleinteile |
| box label | Box-Etikett |
| rebuild / clone | Neu erstellen / Klonen |
| print bed / plate / prime tower / purge (volume) / filament | Druckbett / Druckplatte / Reinigungsturm / Spülvolumen / Filament |
| connection holes (baseplate) | Verbindungslöcher |
| fill area / fill pieces (baseplate) | Füllfläche / Füllstücke |
| skeletonized / light / full (baseplate type) | Skelettiert / Leicht / Voll |

## Command names

*Gridkeeper Behälter*, *Gridkeeper Grundplatte*, *Gridkeeper Einleger*, *Gridkeeper Box*, *Gridkeeper Box-Etikett*,
*Gridkeeper Export*, *Gridkeeper Einstellungen*, *Gridkeeper neu erstellen*, *Gridkeeper klonen*, *Gridkeeper Updates*.
