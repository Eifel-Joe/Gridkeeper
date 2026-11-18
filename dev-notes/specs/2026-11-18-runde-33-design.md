# Runde 33: Entwicklerbefehle im Worktree (p320), Selbst-Neustart messen (p321)

Stand 18.11.2026. Grundlage: Punkte p320/p321 der Liste, Spec `2026-11-17-update-hinweis-design.md` (E13, Messung
Neu-Laden), des Nutzers Festlegung vom 18.11. zu p321 („Zuerst messen“ auf einer Testkopie, kein Test-Release, kein Tag).

## p320 „Testbefehle fehlen, wenn Gridkeeper aus einem Git-Worktree läuft“

**Problem:** `config.DEV_TOOLS` prüft `os.path.isdir(<Add-in-Ordner>/.git)`. In einem Git-Worktree ist `.git` eine
Datei, die Entwicklerbefehle (Snapshot-Tests, Modellbilder, `commands/__init__.py`) fehlen dort.

**Entscheidung:** `config.DEV_TOOLS` nutzt dieselbe Prüfung wie die Update-Sperre: `updateInstall.isGitCheckout`
(`.git` existiert, Datei oder Ordner). Eine Stelle für die Regel, keine Zweitfassung.
- Verworfen: nur `isdir` → `exists` in config.py ändern. Zwei Kopien derselben Regel, die wieder auseinanderlaufen.
- `lib/updateInstall.py` importiert nichts vom Add-in (nur Standardbibliothek), ein Import aus `config.py` erzeugt
  keinen Zyklus. Wie `config.py` es lädt, entscheidet der Plan nach dem Import-Stil der übrigen Module.

**Nicht dabei:** Änderungen an der Update-Sperre selbst, an den Entwicklerbefehlen oder an `DEBUG`.

**Ende-zu-Ende:** pytest: `DEV_TOOLS` ist wahr für einen Add-in-Ordner mit `.git`-Ordner und mit `.git`-Datei,
falsch ohne `.git`. In Fusion (Klicktest der Hauptsitzung, Add-in aus `wt-r33`, ein Worktree): unter Utilities ›
Add-Ins stehen „Gridkeeper tests: run“ und der Modellbilder-Befehl.

## p321 „Nach einem Update Gridkeeper per Knopf neu laden“ — nur Messung

**Frage:** Kann das laufende Gridkeeper sich selbst über `app.scripts` → `Script.stop()` / `Script.run()` neu starten,
so dass danach die neue Version mit allen lebenden Befehlen läuft? Aus einem fremden Skript ist das belegt (E13, W3).
Aus dem Add-in selbst nicht: der Code, der `stop()` aufruft, gehört zu dem Add-in, das gerade entladen wird.

**Messaufbau (Testkopie, des Nutzers Vorgabe):**
1. Testkopie: die Release-Dateien von `wt-r33` (wie `release.yml`) nach
   `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\Gridkeeper-r33test\`, Manifest-Version 9.9.1. Zusätzlich nur in
   der Kopie eine Messsonde `selfRestartProbe.py`, die `run()` der Kopie einbindet (nicht im Repo-Code):
   - schreibt bei jedem Start eine Zeile in `probe.log` der Kopie (Zeit, Manifest-Version, `id()` des Moduls),
   - registriert ein Custom Event `GridkeeperR33SelfRestart`; sein Handler sucht das eigene `Script` (über `folder`)
     und ruft `stop()`, dann `run()`; Rückgaben, `isRunning` und Ausnahmen gehen in `probe.log`.
   Der Handler läuft im Add-in, so wie später ein Knopf im Updates-Dialog (dort ebenfalls über ein Custom Event,
   damit der Dialog-Handler zurückkehrt, bevor das Add-in stoppt).
2. Slot-Job A (~10 s): Git-Add-in (`D:\Entwicklung\Gridfinity\Gridkeeper`) per `Script.stop()` stoppen (gleiche
   Befehls-IDs), Testkopie mit `scripts.addExisting` eintragen und `run()`; `probe.log` zeigt Start 1.
3. Slot-Job B (~5 s): vor dem Neustart die Manifest-Version der Kopie auf 9.9.2 setzen (simuliert das Update),
   `app.fireCustomEvent('GridkeeperR33SelfRestart')`.
4. Slot-Job C (~10 s): `probe.log` lesen (Start 2 mit 9.9.2 und neuem Modul?), `isRunning`, dann je Befehl Bin,
   Baseplate, Label, Box, Updates `commandDefinitions.itemById(id).execute()` und prüfen, dass `ui.activeCommand`
   dieser Befehl ist, danach `terminateActiveCommand` (W4 zeigte: Befehle tot, Dialog öffnet nicht).
5. Aufräumen (Job D, ~10 s): Testkopie `stop()`, `unlink()`; Git-Add-in `run()`; per Bash Kopie-Ordner löschen.
   Prüfen: `Gridkeeper` aus `D:\Entwicklung\Gridfinity\Gridkeeper` läuft, „Beim Start“ unverändert an.
Ein Slot, vier Jobs, Ablauf vorher der Hauptsitzung zeigen. Kein Dokument nötig (kein Bau), des Nutzers Dokumente bleiben.

**Auswertung:**
- **Geht** (Start 2 mit 9.9.2, alle fünf Befehle aktiv): Knopf „Reload Gridkeeper“ im Updates-Dialog bauen (eigene
  Spec-Ergänzung, der Hauptsitzung vorlegen), Klicktest in Fusion.
- **Geht nicht** (Ausnahme, Add-in bleibt gestoppt, alter Code, tote Befehle): Punkt mit Befund schließen, Messung
  in `2026-11-17-update-hinweis-design.md` unter „Messung Neu-Laden“ ergänzen, der heutige Hinweis bleibt; Satz für
  die Liste über die Hauptsitzung. Nur p320 als PR.
- Geht ein Job anders als erwartet schief (Fusion hängt, Dialog): Aufräumen sofort, Befund melden, kein zweiter
  Versuch ohne Rücksprache.

**Nicht dabei:** Test-Release, Tag, Änderung am Update-Installer, Fusion-Neustart durch das Add-in, W4.

## p321 Ergänzung nach der Messung: Knopf „Reload Gridkeeper“ (zur Freigabe)

Messung (18.11., Update-Spec „Messung Selbst-Neustart“): Gridkeeper kann sich aus einem eigenen Custom-Event-Handler über
`app.scripts` → eigenes `Script.stop()`/`run()` neu starten, danach läuft die neue Version mit allen Befehlen. Damit greift
Update-Spec E13: „gibt es einen sicheren Weg ohne Neustart, bekommt die Erfolgsmeldung einen Knopf dafür“.

**R1 Wo:**
- Erfolgsmeldung nach dem Update: statt OK-Meldung eine Ja/Nein-Frage „Gridkeeper X is installed. Reload Gridkeeper now
  to use it?“ (Ja = neu laden, Nein = Text wie heute mit den Handwegen).
- Dialog „Gridkeeper updates“: ein Knopf „Reload Gridkeeper“ (BoolValue-Button wie „Check now“), sichtbar, solange
  laufende und installierte Version verschieden sind (E13a). Die Versionszeile nennt den Knopf zuerst, dann die Handwege.
**R2 Ablauf:** Der Klick feuert ein eigenes Custom Event `…_reload` und kehrt zurück (Gridkeeper beendet sich nie im
  eigenen Befehls-Handler). Der Event-Handler wartet, bis kein Gridkeeper-Befehl mehr aktiv ist (`ui.activeCommand`;
  sonst neuer Versuch über einen Timer wie beim Update-Dialog, höchstens 10×), sucht das eigene `Script` **über den
  Ordner** (nie über den Namen; Klon und Worktree heißen beide „Gridkeeper“), ruft `stop()`, dann `run()`.
**R3 Fehler:** kein oder mehr als ein eigenes Script, `stop()`/`run()` `False` oder Ausnahme → Meldung mit den Handwegen
  (Fusion neu starten, Stop/Run in Scripts and Add-Ins). Nach einem gescheiterten `run()` läuft Gridkeeper nicht mehr, die
  Meldung sagt das.
**R4 Git-Checkout:** unverändert kein Update; der Knopf erscheint auch dort, sobald laufende und Manifest-Version
  abweichen (z. B. nach `git pull` mit neuer Version), da der Weg derselbe ist.
**R5 Fusion-frei testbar** (lib/updateCheck bzw. lib/updateInstall): Sichtbarkeit (laufend ≠ installiert), Auswahl des
  eigenen Scripts aus (Ordner, Script)-Paaren mit Normalisierung von Groß-/Kleinschreibung und Schrägstrichen, Texte.

**Nicht dabei:** Fusion-Neustart durch das Add-in, Neu-Laden von Modulen im Prozess (W4), automatisches Neu-Laden ohne
Klick, Änderungen am Installer.

**Ende-zu-Ende:**
- pytest für R5.
- Fusion (ein Slot): Testkopie wie bei der Messung, diesmal **ohne Sonde**, Manifest 9.9.1, dann 9.9.2 setzen, das
  Produkt-Event `…_reload` feuern; danach `runningVersion (9, 9, 2)` im neuen Modul und fünf Befehle aktiv. Aufräumen wie
  bei der Messung.
- Klicktest der Hauptsitzung im echten Dialog: Updates-Dialog zeigt „Reload Gridkeeper“ nur bei abweichender Version
  (dafür das Manifest der geladenen Kopie von Hand hochsetzen), Klick → Dialog schließt, Gridkeeper startet neu,
  Dialog zeigt danach „Running … <neue Version>“.
