# Klicktest Runde 33

Beide Add-ins heißen „Gridkeeper“ und haben dieselben Befehls-IDs: immer nur eins laufen lassen.

| Schritt | Erwartet |
|---|---|
| Gridkeeper aus `D:\Entwicklung\Gridfinity\Gridkeeper` stoppen, das aus `D:\Entwicklung\Gridfinity\wt-r33` starten (ein Git-Worktree: dort ist `.git` eine Datei) | startet ohne Fehlermeldung |
| Utilities › Add-Ins aufklappen | „Gridkeeper tests: run“, „Gridkeeper tests: update snapshots“ und „Gridkeeper docs: render models“ stehen da (p320; vorher fehlten sie im Worktree) |
| „Gridkeeper tests: run“ anklicken | Das Testfenster öffnet sich mit der Fallliste (kein Dialog); keinen Lauf starten, Fenster schließen |
| Gridkeeper aus `wt-r33` stoppen, das aus `D:\Entwicklung\Gridfinity\Gridkeeper` wieder starten | Die drei Befehle stehen dort wie bisher (Klon, `.git` ist ein Ordner) |
