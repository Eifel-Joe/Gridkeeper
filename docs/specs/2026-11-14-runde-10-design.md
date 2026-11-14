# Runde 10 – Madenschrauben und eingefärbte Beschriftung

Stand 2026-11-14. Ergänzt `2026-11-14-cullenect-labels-design.md`. Punkte p85 „Madenschrauben als Schrauben-Symbol“
und p86 „Beschriftung wahlweise direkt einfärben (Einleger und Bin-Labels)“. Jörgs Entscheidungen in der Sitzung
(14.11.): Madenschraube Variante B (Stirnseite abgesetzt), Lizenz MIT, p86-Konzept „Ja, so bauen“.

## p85 Madenschrauben

### Befund
- `cullenectCatalog.isValidScrew` verbietet Kopf `none` mit Antrieb (wie Cullenect). Kopflos gibt es nur glatte
  Gewindestifte (`driver none`).
- Der Dialog bietet jede Kombination der Bausteine an, auch solche ohne svg („No svg for this symbol“, OK gesperrt).

### Entscheidung
- Kopf `none` mit Antrieb `slot`, `hex` oder `torx` ist eine Madenschraube. Zeichnung: Gewinde wie bei Cullenect
  (`cullenect_shaft`), daneben 1 mm abgesetzt die Stirnseite als Kreis Ø 6 mm mit dem Antrieb (Cullenect-Form auf 70 %).
  Schaft `machine` = flaches Ende, `tapping` = Spitze (Cullenects Schaftformen). Nur Vollgewinde, kein Flansch,
  Sicherheitsstift bei `hex` und `torx`. 10 Symbole, 15,56 mm breit (übrige Schrauben 14,56 mm).
- Eigener Ordner `cullenectIcons/setscrews/` mit `README.md` und `LICENSE` (MIT, eigene Arbeit dieses Forks; Gewinde-
  und Antriebsformen per `use <Cullenect.scad>`, MIT, CullenJWebb). Gleiches Namensschema `screw_none_…svg`, der Katalog
  liest beide Ordner.
- Erzeugt von `tools/setScrewIcons.py` (Vorlage `tools/setscrew/SetScrew.scad`), wie `tools/cullenectIcons.py`.
- Dialog: Jede Auswahlliste bietet nur Werte an, die mit den übrigen gewählten Bausteinen ein svg ergeben. Ändert sich
  ein Baustein so, dass die Wahl eines anderen ungültig wird, springt dieser auf den ersten passenden Wert (Reihenfolge:
  Kopf, Schaft, Gewinde, Antrieb). Flansch und Sicherheitsstift werden gesperrt, wenn sie nicht gehen, und abgewählt.

### Nicht dazu
- Weitere Spitzenformen (Ring-/Zapfenschneide), andere Antriebe für Madenschrauben.

## p86 Beschriftung einfärben

### Entscheidung
- Dialog Einleger und Bin: Dropdown „Text color“: None (wie bisher), Black, White, Red, Orange, Yellow, Green, Blue,
  Gray, Custom. Bei Custom ein Feld `#rrggbb`; ungültige Eingabe sperrt OK mit Hinweis.
- Im Zustand steht die Farbe als `#rrggbb`, leer = keine (`textColor` beim Einleger, `labelColor` bei der Bin).
- Darstellung sprachunabhängig: Aus den Bibliotheken die erste Darstellung mit änderbarer Grundfarbe, deren Name mit
  „Plastic“ bzw. „Kunststoff“ beginnt, sonst die erste mit änderbarer Grundfarbe. Kopie ins Dokument als
  `Gridfinity label RRGGBB`, Farbe gesetzt, bei Wiederholung wiederverwendet.
- Einleger: Text- und Symbolkörper bekommen die Darstellung (bei Debossed auch die verborgenen Füllkörper).
- Bin-Labels: Embossed mit Farbe wird nicht mit der Bin vereint, die Buchstaben bleiben eigene Körper. Engraved und
  Outline schneiden wie bisher, die Werkzeugkörper bleiben als bündiges Inlay stehen. Die Körper heißen
  `<Label-Name> text N` (von links nach rechts), werden mit der Bin verschoben und vom Bin-Befehl zurückgegeben.
- Ohne Farbe ändert sich nichts (bestehende Snapshots gleich).

### Nicht dazu
- Flächenfarben auf dem Bin-Körper; Farbe getrennt für Text und Symbol; Farbe für Cullenect-Taschen.
- Nach einer späteren Text-Änderung (Text-Parameter) neue Buchstabenkörper nachfärben: Fusion legt sie an, ob sie die
  Farbe erben, wird im Fusion-Lauf geprüft und dokumentiert.

## Prüfung (Ende-zu-Ende)
- pytest: Katalog (Madenschrauben gültig, Optionen pro Teilauswahl), Werkzeug (scad-Text, Jobs), Farblogik
  (Presets, Custom, Darstellungsname, Wahl der Basis-Darstellung), Testfall-Laden mit neuen Feldern.
- Fusion-Snapshot-Lauf: keine neuen Fehler (bekannt rot: 4 Text-Label-Bin-Fälle). Neue Fälle
  `label_1u_set_screw_hex`, `label_1u_screw_text_colored`, `bin_2x1x3_label_text_engraved_colored`,
  `bin_2x1x3_label_icon_text_embossed_colored`; der Lauf prüft bei Farbfällen die Darstellung der Beschriftungskörper.
- 3MF-Export eines eingefärbten Bins: prüfen, dass die Beschriftung eigene Objekte sind (und ob Farbe mitkommt).
