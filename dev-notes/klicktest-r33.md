# Klicktest Runde 33

Beide Add-ins heißen „Gridkeeper“ und haben dieselben Befehls-IDs: immer nur eins laufen lassen.

| Schritt | Erwartet |
|---|---|
| Gridkeeper aus `D:\Entwicklung\Gridfinity\Gridkeeper` stoppen, das aus `D:\Entwicklung\Gridfinity\wt-r33` starten (ein Git-Worktree: dort ist `.git` eine Datei) | startet ohne Fehlermeldung |
| Utilities › Add-Ins aufklappen | „Gridkeeper tests: run“, „Gridkeeper tests: update snapshots“ und „Gridkeeper docs: render models“ stehen da (p320; vorher fehlten sie im Worktree) |
| „Gridkeeper tests: run“ anklicken | Das Testfenster öffnet sich mit der Fallliste (kein Dialog); keinen Lauf starten, Fenster schließen |
| Gridkeeper aus `wt-r33` stoppen, das aus `D:\Entwicklung\Gridfinity\Gridkeeper` wieder starten | Die drei Befehle stehen dort wie bisher (Klon, `.git` ist ein Ordner) |

## Reload Gridkeeper (p321)

Gridkeeper aus `wt-r33` läuft (wie oben). Vorher `Gridkeeper.manifest` im Ordner `wt-r33` von Hand auf `1.1.1` setzen
(simuliert eine neue Version auf der Platte; danach mit `git checkout Gridkeeper.manifest` zurücksetzen).

| Schritt | Erwartet |
|---|---|
| Utilities › Add-Ins › Gridkeeper updates | Text „Running Gridkeeper 1.1.0, installed 1.1.1. Click Reload Gridkeeper, or restart Fusion, …“; Knöpfe „Reload Gridkeeper“ und „Close“ |
| „Reload Gridkeeper“ klicken | Dialog schließt, kurz danach steht Gridkeeper wieder im Menü, keine Fehlermeldung |
| Gridkeeper updates erneut öffnen | „Running Gridkeeper 1.1.1.“, nur „Close“ |
| Gridkeeper bin öffnen, Abbrechen; Gridkeeper box öffnen, Abbrechen | beide Dialoge öffnen sich (Befehle leben nach dem Neu-Laden) |
| Manifest zurücksetzen, Gridkeeper updates öffnen | „Running Gridkeeper 1.1.1, installed 1.1.0. Click Reload Gridkeeper…“ (auch ältere Version auf der Platte), mit Reload zurück auf 1.1.0 |
| Gridkeeper updates mit gleicher Version | kein „Reload Gridkeeper“-Knopf |
| Manifest wieder auf `1.1.1`, Gridkeeper updates öffnen, **Close** klicken | Dialog schließt, Gridkeeper lädt **nicht** neu (erneut öffnen: weiter „Running Gridkeeper 1.1.0, installed 1.1.1“) |
| Siehe Teil B unten: Erfolgsfrage nach einem echten Update | |
| Steht zugleich ein Update an (nur prüfbar, wenn GitHub ein neueres Release hat; sonst überspringen) | Dialog aus dem Menü: „Update now“ im Dialog und OK „Reload Gridkeeper“ getrennt; der von der Update-Prüfung geöffnete Dialog zeigt nur „Update now“/„Later“ |

### Teil B: Erfolgsfrage nach einem Update, langes Warten (p321)

Die Frage „Reload Gridkeeper now to use it?“ kommt nur nach einem echten Update, und ein Git-Checkout wird nie
aktualisiert. Darum mit einer Kopie ohne `.git`:
`python dev-notes/tools/r33-self-restart/build_copy.py --no-probe` baut sie im Fusion-AddIns-Ordner aus `wt-r33`; ihr
Manifest von Hand auf `1.0.0` setzen (dann bietet GitHub 1.1.0 an). Git-Add-in stoppen, Kopie in Scripts and Add-Ins
starten.

| Schritt | Erwartet |
|---|---|
| Gridkeeper updates → Check now | „Gridkeeper 1.1.0 is available (you have 1.0.0)“, „Update now“ sichtbar |
| Update now | Fortschritt, dann Frage „Gridkeeper 1.1.0 is installed. Reload Gridkeeper now to use it? …“ mit Ja/Nein |
| **Ja**, Dialog **mindestens eine Minute offen lassen** (z. B. Release notes lesen) | Dialog sagt „… Close this dialog to reload Gridkeeper and use 1.1.0.“, **keine** Abbruchmeldung erscheint |
| Close | Gridkeeper lädt neu; Gridkeeper updates zeigt danach „Running Gridkeeper 1.1.0.“ (ab hier läuft der Release-Code 1.1.0) |
| Aufräumen | Kopie stoppen, `build_copy.py --remove`, Git-Add-in wieder starten |
