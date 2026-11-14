# Runde 7 – lose Trennwände, Haken in „Bin compartments“, Einleger als Komponente

Stand 2026-11-14. Ergänzt `2026-11-14-trennwaende-bis-oben-design.md` (p17). Punkte p82, p80, p81.

## p82 „Hochgezogene Trennwände: bei zwei parallelen Trennwänden bleibt die zweite lose und zu kurz“

**Ursache (Hauptsitzung belegt):** `createRaisedDividers` vereint alle Klötze per Combine/Join zu einem Körper.
Fusion vereint Körper, die sich nicht berühren, nicht. Nur der erste Klotz kommt zurück und in die Bin,
die anderen bleiben als „Raised dividers (1)“ … lose liegen.

**Fix:** Kein Join der Klötze untereinander. Jeder Klotz wird einzeln vom Fuß-Schnitt beschnitten
(Werkzeugkörper bis zum letzten Schnitt behalten), alle entstandenen Körper gehen in die Liste, die in die
Bin vereint wird. Jeder Klotz steht auf einer Fächerwand und berührt damit den Bin-Körper.

**Schwester-Pfade:** Alle `joinBodies`-Aufrufe auf die Annahme „Join ergibt einen Körper“ geprüft
(Ergebnis im Plan, Task 4).

**Prüfung:** Der Snapshot-Lauf schlägt künftig fehl, wenn das Dokument eines Falls Körper enthält, die der
Generator nicht zurückgibt (lose Körper). Neue Fälle: 3×2×3-Bin mit 3 Fächern nebeneinander, Haken an –
einmal hybrid, einmal in Bauteilkonstruktion (neues optionales Feld `designIntent` im Fall, Standard hybrid).
Live: zwei solche Bins in einem Bauteil-Dokument, danach genau zwei Körper, keiner „Raised dividers*“.

## p80 „Haken „Dividers up to the top“ in den Bereich Bin compartments verschieben“

Der Haken steht in der Gruppe „Bin compartments“ (unter „Edit compartment layout“) statt unter „Bin features“.
Aktiv nur, wenn zusätzlich die Bin mehr als ein Fach hat (Fächer X × Y > 1, gefaltete Wände zählen als ein
Fach). Die Input-ID bleibt `dividers_to_top`, gespeicherte Defaults und Snapshot-Fälle gelten weiter.

## p81 „Label-Befehl: Einleger als eigene Komponente statt als Körper in der Bauteilkonstruktion“

Befund: Bin, Baseplate und Label legen nur in der hybriden Konstruktion eine Komponente an, sonst einen
Körper in der Wurzel (auch in der Baugruppe). Bauteilkonstruktion erlaubt keine zweite Komponente
(Fusion-Meldung in einem Testdokument belegt). Per API lässt sich ein Bauteil-Dokument auf hybrid umstellen,
auch mit vorhandenen Körpern. Optionen sind Jörg vorgelegt, **Entscheidung offen** – Umsetzung erst nach seiner Wahl.

## Nicht-Ziele
- Keine Änderung der Form der Trennwände, keine Änderung bestehender Snapshots außer wo der Fix es erzwingt.
