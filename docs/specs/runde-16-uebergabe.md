# Runde 16 – Übergabe

Stand 2026-11-15. Branch `runde-16` (von `runde-14-18` 51a1bb4), nicht gepusht, nicht gemergt. Spec
`docs/specs/2026-11-15-runde-16-design.md` (von Jörg freigegeben), Plan `docs/plans/2026-11-15-runde-16.md`
(023fe0a, von der Hauptsitzung freigegeben).
Punkte: p30 „Snapshot-Tests der Text-Labels passen auf diesem Rechner nicht“, p31 „Vorschaubilder der Snapshot-Tests
fehlen“, p34 „Skizzen-Prüfung im Testlauf robuster machen“, p32 „Gridfinity settings zeigen bei Cullenect die echte
Laschenbreite“, p33 „Taschenliste in den Einstellungen anders beschriften“.

## Stand je Punkt

| Punkt | Stand | Beleg |
|---|---|---|
| p30 | umgesetzt (476e4e1): Text-Label-Fälle nach Form (Körperanzahl, Gesamtvolumen, Ausmaße aller Körper); eine Einstellung, die der Snapshot nicht hat, zählt nur abseits ihres Defaults | pytest; Snapshot-Lauf 83/83, kein Snapshot neu abgelegt (vorher 79/83) |
| p34 | umgesetzt (476e4e1): Prüfungen nach dem Bau über `testCases.runChecks`, eine Ausnahme wird „check <name> failed“; der Vergleichsbau mit Parametern von Anfang an wird auf Skizzen geprüft | pytest `test_a_broken_check_is_a_check_failure`; Snapshot-Lauf grün |
| p31 | umgesetzt (828dfc1): Darstellung sprachunabhängig über `appearanceUtils.baseAppearance`, ohne Darstellung Standarddarstellung; gilt auch für die Modell-Screenshots | pytest `tests/test_viewport_pictures.py` (deutsche Bibliothek: vorher rot, jetzt grün). In Fusion greift die Suche (`r16_preview`: statt „no appearance starting with Plastic“ jetzt „the Gridfinity tests palette is closed“); das Bild selbst braucht die offene Test-Palette → Handtest |
| p32/p33 | umgesetzt (c5519cd): Cullenect-Abschnitt mit „Label tab width … mm (built)“ und je Größe „1U: 8 sockets, pocket …, insert …“, zu kurze Fächer als „No socket“ | pytest; Anzeige entsteht nur im Dialog → Handtest |

## Belege

- **pytest:** `743 passed` (Stand f43fccd).
- **Snapshot-Lauf** (`r16_snap`, 15 Häppchen, Stand `r16_reload1` = Code von 828dfc1, p31 war beim Reload schon im Arbeitsstand): „DONE 83 cases,
  not green: []“. Vorher (R15) 79/83, rot nur die vier p30-Fälle. Kein Snapshot neu abgelegt, keine Vorschaubilder
  verändert (`git status` sauber, `r16_preview` schreibt nur in einen Temp-Ordner).
- **Vorschau** (`r16_preview_red` alter Stand): „preview not taken, no appearance starting with Plastic - Matte or
  Plastic in the material libraries“; neuer Stand (`r16_preview`): „the Gridfinity tests palette is closed, nothing to
  finish the picture“ – die Darstellungssuche ist nicht mehr das Hindernis.

## Review (Opus)

Kein kritischer Fund. Umgang:
- **Wichtig, behoben (f43fccd):** Der Formvergleich allein ließ einen verschobenen Tab oder ein Fach-Label unter dem
  falschen Fach mit gleichem Volumen und gleicher Hülle durch. Jetzt wird jeder Körper eines Text-Label-Falls wieder
  abgezogen; übrig bleiben darf beidseits nur eine Schicht so dünn wie die Buchstaben (z-Ausdehnung ≤ 0,6 mm,
  `testCases.isLetterSlab`), dazu gleiche Stückzahl; der Formvergleich bleibt zusätzlich. Fusion (`r16_reload2`):
  alle sechs Text-Label-Fälle grün (`r16_snap_t1`–`t3`, die vier p30-Fälle und die zwei farbigen).
- **Klein, behoben:** (3) Fach-Labels machen einen Fall nur mit sichtbarem Fach-Layout zum Text-Fall, wie der Builder
  sie nimmt. (4) Die Diff-Ansicht eines roten Text-Falls hat wieder Körper mit Resten. (5) Die Modell-Screenshots
  zeichnen ohne Darstellung in Fusions eigener Darstellung, wie die Vorschauen.
- **Klein, bleibt:** (2) Eine Einstellung, die ein alter Snapshot nicht hat, zählt am jeweiligen Default nicht; ändert
  sich dieser Default später, meldet der Einstellungsvergleich das bei diesen Snapshots nicht (die Form schon). Beim
  nächsten Neuablegen bekommen sie die Schlüssel. (6) „too short for a Cullenect pocket“ steht auch bei zu schmalen
  Fächern, wie bisher in `describeSocket`. Eine Bin mit Rissen verwirft Fach-Labels ebenfalls, das prüft
  `isTextLabelCase` nicht nach.

## Handtest für Jörg (Testtermin)

1. Utilities › Add-Ins › „Gridfinity tests: update snapshots“ für einen Fall (Test-Palette offen): Das Vorschaubild
   entsteht (p31).
2. Bin mit 8 gleichen Fächern, Cullenect, bauen, Rechtsklick „Gridfinity settings“: Abschnitt Cullenect zeigt die
   gebaute Laschenbreite (mindestens 14 mm) und „1U: 8 sockets, …“ (p32, p33).
