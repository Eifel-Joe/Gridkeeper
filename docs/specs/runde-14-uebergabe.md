# Runde 14 – Übergabe

Stand 2026-11-15. Branch `runde-14` (von `runde-14-18` 6321253), nicht gepusht, nicht gemergt. Spec
`docs/specs/2026-11-15-runde-14-design.md` (von Nutzer freigegeben), Plan `docs/plans/2026-11-15-runde-14.md` (5f3e381,
von der Hauptsitzung freigegeben).
Punkte: p72 „Bin-Labels: Text mit mehr Buchstaben kann beim Ändern verrutschen“, p120 „Eingefärbte Beschriftung: nach
Textänderung sind neue Buchstaben nicht eingefärbt“, p71 „Einleger: nach Textänderung neue Buchstaben ohne Namen und
Kennung“, p53 „Mehrfarbdruck: Text und Symbol sind mehrere Körper“.

## Ergebnis je Punkt

| Punkt | Stand | Beleg |
|---|---|---|
| p72 | umgesetzt: Text von Bin- und Fach-Labels entsteht an der fertigen Stelle, Schnitt/Vereinen in der Extrusion; farbige Buchstaben gleich an der Stelle, an die die Bin verschoben wird | E2E a–g ALL OK, f/g vorher ROT |
| p120 | umgesetzt: Farbe an der Text-Occurrence, neue Buchstaben zeigen sie, auch im 3MF | Probe Q5, E2E b, d, e, f, g |
| p71 | umgesetzt: Rechtsklick auf einen Buchstaben in „Text“ findet Bin bzw. Einleger; neue Buchstaben heißen wie von Fusion vergeben („Körper7“, Nutzer 15.11.) | pytest, E2E c |
| p53 | **offen**: 3MF zeigt jeden Buchstaben als eigenes Objekt, keine Gruppe „Text“ | Probe Q5, siehe unten |

## Belege

- **pytest:** `python -m pytest -q` → `712 passed in 5.02s` (Stand 06646a8).
- **Hinweisfenster-Test (Task 1):** durchgeführt von der Hauptsitzung, weil diese Sitzung kein Fusion-MCP hatte.
  `messageBox` per Skript, `fusion-hinweis-schliessen.sh` im Hintergrund: Fenster geschlossen, Skriptaufruf kehrte
  zurück, exit 0. Zeile in `D:\Entwicklung\Gridfinity\fusion-hinweise.log` (hier nachgelesen):

      2026-11-15 19:04:35 GESCHLOSSEN Fenster 'Gridfinity Test' Texte: [Gridfinity Test / Runde 14 Hinweistest: wird automatisch geschlossen] Knoepfe: [OK]

- **Ende-zu-Ende** `tests/e2e/runde14_labels.py`, in Gruppen unter 50 s (Fusion-MCP-Zeitlimit), Stand nach
  Reload 5 (= 06646a8): a ALL OK (25 Punkte, 30,4 s), b ALL OK (18), c ALL OK (15), d ALL OK (19), e ALL OK (11),
  f ALL OK (11), g ALL OK (10). Vor der Review-Korrektur (Stand 7593730): f und g je `1 FAILED`, „all letters on the
  tab: … y 26.92..76.04“ bzw. „y 26.83..75.42“ (neue Buchstaben der zweiten Bin an der unverschobenen Stelle).
  Ausgaben in `D:\Entwicklung\Gridfinity\fusion-auftraege\r14_e2e_*.out`.
- **Snapshot-Lauf** (alle 83 Fälle, Auftrag `r14_snap` in 17 Häppchen, Stand 7593730): 75 grün. Nicht grün:
  die vier p30-Fälle und vier Label-Fälle. Wiederholt mit dem Stand nach Reload 5 (`r14_snap_l1`–`l4`), siehe unten.
  Nach dem Neuablegen (`r14_refresh_1`/`_2`) Kontrolllauf `r14_snap_l1`–`l4`: `icon_text_embossed_colored`,
  `text_engraved_colored`, `tab_steep_tilted`, `compartments_4x3` pass; rot nur die vier p30-Fälle. **Stand 79 von
  83 grün.**
- **Review** (Opus-Subagent): 1 kritischer, 2 wichtige, 5 kleinere Funde, Umgang siehe unten.

## Snapshots

Alle acht nicht grünen Fälle haben ein Bin-Label mit Text. In allen acht ist das Volumen je Körper gleich (gleiche
Stückzahl der Differenz, Abweichung ≤ 0,005 mm³) und die Größe der Bounding-Box je Körper gleich; nur die Lage des
Label-Texts weicht ab. Ursache: Text auf einer Grundlinie statt in einer Box mit Mitte-Ausrichtung.

| Fall | Abweichung (Stand Reload 5) | Entscheidung |
|---|---|---|
| `bin_2x1x3_label_icon_text_embossed_colored` | Text y −0,063 mm, Icon y +0,064 mm, x gleich (≤ 0,000003 mm) | neu abgelegt |
| `bin_2x1x3_label_text_engraved_colored` | Text y −0,082 mm, x +0,053 mm, hinter dem Leerzeichen +0,19 mm (Laufweite entlang der Linie) | neu abgelegt |
| `bin_3x2x6_tab_steep_tilted` | 0,001 mm³ in 2 Stücken, gleiche Bounding-Box: gleich, Icon nicht gespiegelt | neu abgelegt |
| `bin_4x3x3_compartments_4x3` | 0,003 mm³ in 24 Stücken über 12 Fach-Labels | neu abgelegt |
| `bin_2x1x3_label_icon_text_embossed`, `bin_2x1x3_label_text_engraved`, `bin_2x3x5_features`, `bin_2x3x5_features_params_all` | p30 („built with other settings than the snapshot“), dazu dieselbe Label-Lage wie oben | nicht angefasst (R16) |

Neu abgelegt per Skript (`stageSnapshots` mit stummem Fortschritt, Kopieren wie `applyPendingUpdate`): ein erster
Versuch über `refreshSelected` scheiterte, weil ohne vorherigen Bericht `lastReport` None war, und blockierte Fusion
knapp 10 Minuten mit einem Hinweisfenster (von der Hauptsitzung geschlossen). Diff der `fingerprint.json` geprüft:
gleiche Körper und Größen, Volumen ≤ 0,000009 verschieden, nur die Lageverschiebungen der Tabelle. Vorschaubilder
entstanden keine (p31); die Ablage hatte die vorhandenen von `tab_steep_tilted` und `compartments_4x3` gelöscht, sie
sind samt README-Zeilen aus Git wiederhergestellt, weil die Form gleich ist.

Vor der Korrektur lag Text hinter einem Icon 0,8 mm zu weit rechts (Abstand Icon–Text 2,6 statt 1,8 mm): Text entlang
einer Linie beginnt um den Vorlauf des ersten Buchstabens später. `_baselineTexts` misst jetzt die Buchstabenkante und
setzt den Linienanfang um die Differenz früher.

## Probe (Task 2)

Aufträge `r14_probe` bis `r14_probe5` in `D:\Entwicklung\Gridfinity\fusion-auftraege` (Skript und `.out` dort).
Gemessen an einer 2x1x3-Bin, Label „AB“ → „ABCDE“, `heightUnit` 7→10 mm, `baseWidth`/`baseLength` 42→50 mm.

- **Q1 mitlaufende Ebene, hält:** Text auf einer Grundlinie auf einer Ebene mit Offset-Ausdruck folgt Höhe (+9 mm),
  Breite (+8 mm) und Länge (+8 mm), behält alle Buchstaben. Auch Box-Text verlor nichts; der Verlust aus Commit 073efbe
  ließ sich nicht nachstellen.
- **Kippung:** `setByAngle` kippte nach der Höhenänderung zur anderen Seite, untauglich. Eine Ebene durch drei
  Konstruktionspunkte aus Offset-Ebenen blieb gleich. Mit der Punktreihenfolge der Probe zeigte ihre Normale nach unten
  (Text von oben gespiegelt); im Code ist die Reihenfolge so, dass sie nach oben zeigt, das E2E prüft es.
- **Q2 Skizzenkoordinaten:** Ursprung = Projektion des Komponenten-Ursprungs; Skizzen-x kann gegen Modell-x laufen.
  Abstandsmaße vom Ursprung sind Beträge.
- **Q3 Schnitt/Vereinen in der Extrusion, hält:** Cut (auch dünn 0,001 mm) und Join nach oben mit
  `participantBodies=[Bin]` nehmen neue Buchstaben mit, keine losen Körper. Farbiger Zwillingsschnitt aus „Text“ mit
  der Bin als Proxy hält auf 30°. Das alte Label ließ nach „ABCDE“ jedes Mal 4 lose Körper in der Bin.
- **Q4 Icon:** fixierte Kurven folgen x nicht (1. Versuch), Ankermaße scheiterten an Überbestimmung (2.), Fixierung
  lösen plus Ankermaße hält (3.): Sechskantmutter 10 Punkte, 20 Maße in 0,3 s; `cullenect-crimp-ring-closed`
  263 Punkte, nach 60 s erst 414 Maße. Daraus Vorschlag A (unten).
- **Q5 Farbe, hält:** Farbe nur an der Text-Occurrence: neue Buchstaben zeigen sie, 3MF der Bin und von „Text“ allein
  gibt jedem Buchstaben #2060D0. Daher `COLOR_BODIES_TOO = False`.
- **p53:** Im 3MF ist jeder Buchstabe ein eigenes Objekt auf oberster Ebene (Bin: 6 Objekte, 6 Build-Items; „Text“
  allein: 5 Objekte, 5 Build-Items), keine Gruppe „Text“. Nach Entscheidung 4 der Spec nicht erledigt, nichts gebaut
  (Hauptsitzung 15.11.).

## Gesammelte Abweichungen von der Spec

1. **Große Icons werden noch verschoben** (Entscheidung 1: keine Verschieben-Schritte für Icons). Freigegeben von der
   Hauptsitzung als Vorschlag A: Icons bis 40 Punkte (`binLabelLayout.ICON_POINTS_HELD_BY_DIMS`, beim Bau gezählt)
   hängen über Maße an den Parametern, größere (die Cullenect-Symbole, 428–1460 Pfadbefehle) werden als Körper
   verschoben, der Text nie. Die Symbolkörper ändern sich mit dem Text nicht, das Verschieben hält (E2E e, g). Punkt
   p180 „Große Cullenect-Symbole in Bin-Labels werden noch verschoben“.

## Review-Funde (Opus) und Umgang

- **Kritisch, behoben:** Farbige Buchstaben einer Bin, die nicht am Nullpunkt gebaut wird (jede Bin nach der ersten),
  wurden per „Text placement“ verschoben; neue Buchstaben blieben an der unverschobenen Stelle. Jetzt entstehen sie
  an der endgültigen Stelle, der Zwillingsschnitt bleibt dort, wo die Bin gebaut wird. „Bin placement“ verschiebt nur
  die Bin. Belegt mit E2E f/g (vorher ROT, danach grün). Schwester-Pfade geprüft: Einleger entstehen an ihrer Stelle,
  der Joint bewegt die ganze Occurrence; die übrigen Verschieben-Features betreffen keinen Text.
- **Wichtig, behoben:** gekippte Fälle mit Icon und farbigem Schnitt fehlten im E2E → Gruppen f, g.
- **Wichtig, nicht umgesetzt:** reine Funktion für die Matrix der Operationen. Die Kombinationen wirken über
  Fusion-Features, das E2E prüft sie in Fusion; eine reine Matrix prüfte nur das Mapping.
- **Klein, behoben:** `partTag` sucht nur für Körper in einer Text-Komponente (Test
  `test_untagged_body_outside_a_text_component_has_no_part`); Outline-Ausweg gilt für Schnitt und Füllung gemeinsam;
  Kommentar `labelColors.textEditByParameter` nachgezogen.
- **Klein, bleibt:** Bins als Körper in der Wurzel (alte Dokumente, Vorschau) haben keine Text-Komponente: Farbe am
  Körper, neue Buchstaben dort ohne Farbe und ohne Rechtsklick-Erkennung (Fallback der Spec). Unterlängen (g, p, y)
  reichen Richtung Vorderkante, weil die Grundlinie auf die Großbuchstaben mittig gesetzt ist.

## Offen / neue Punkte

- p53 offen (siehe oben). Für des Nutzers Testtermin: Fasst sein Slicer die Körper einer Komponente zusammen?
- p180 „Große Cullenect-Symbole in Bin-Labels werden noch verschoben“.
- p181 „Bin-Label-Text läuft beim Verlängern über den Bin-Rand“: Ein Text, der das Label schon füllt, behält beim
  Verlängern seine Höhe und läuft nach rechts über (E2E: bis 105 mm bei 99,5 mm Bin). Das E2E lässt das nach rechts zu.

## Handtest für Nutzer (Testtermin nach R18)

1. Neues Dokument, zwei Bins mit Label (eine graviert, eine farbig erhaben, eine davon gekippt), dazu ein Fach-Label.
   Text-Parameter um drei Buchstaben verlängern: alle Buchstaben bleiben auf der Lasche, graviert in die Bin, erhaben
   auf ihr, farbig in „Text“ und in der Farbe.
2. Bin mit Sechskantmutter und Text, Basisbreite ändern: Icon und Text wandern zusammen.
3. Farbiger Einleger, Text verlängern, Rechtsklick auf einen neuen Buchstaben: „Gridfinity settings“ zeigt den Einleger.
4. 3MF-Export einer farbigen Bin in den Slicer: Kommen die Buchstaben als ein Teil oder einzeln (p53)?
