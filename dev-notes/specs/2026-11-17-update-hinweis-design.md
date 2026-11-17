# Runde Update-Hinweis: Gridkeeper prüft selbst auf neue Versionen (p310)

Stand 17.11.2026, Entwurf zur Freigabe durch die Hauptsitzung. Branch `claude/update-hinweis-6b49ec` von `master`
(0b0550a). Kommt ins Release 1.1.0; die Manifest-Version ändert diese Runde nicht.

Markierung: **[Nutzer]** = des Nutzers Vorgabe wörtlich oder aus dem Auftrag, **[Vorschlag]** = meine Festlegung, die die
Hauptsitzung freigeben oder ändern soll.

## Punkt und Wortlaut

p310 „Add-in prüft selbst auf neue Gridkeeper-Versionen“.
Nutzer: „Für Updates Variante 2.“ und „Beim Update-Hinweis auch einen Link zu den Versionshinweisen einbauen. Man soll
ja wissen was man bekommt.“

## Warum

Gridkeeper kommt nicht über den App Store; wer die Release-ZIP installiert hat, erfährt von neuen Versionen nur, wenn
er auf GitHub nachsieht. Das Update von Hand (ZIP über den Ordner entpacken) ist fehleranfällig. Nutzer selbst arbeitet
aus einem Git-Checkout, der darf nie angefasst werden.

## Was es heute gibt (Befund)

- Kein Update-Code, kein Netzzugriff im Add-in. `Gridkeeper.py` ruft nur `commands.start()`.
- Manifest-Version `1.0.0`, Release `gridkeeper-v1.0.0` mit Asset `Gridkeeper-v1.0.0.zip`; die GitHub-API liefert je
  Asset ein `digest` (`sha256:…`). Die ZIP enthält genau einen Ordner `Gridkeeper/` (siehe `release.yml`).
- **Gespeicherte Dialog-Vorgaben liegen im Add-in-Ordner** (`commands/*/commandConfig/`), ebenso dürfen Nutzer eigene
  SVG-Symbole in die Symbolordner legen (Doku Symbols). Ein Ordnertausch muss beides mitnehmen.
- Es gibt keinen globalen Einstellungsdialog; „Gridkeeper settings“ zeigt nur die Einstellungen eines Körpers.
- `config.DEV_TOOLS` erkennt den Git-Checkout per `os.path.isdir('.git')`; in einem Git-Worktree ist `.git` eine Datei.

## Anforderungen (Variante 2) [Nutzer]

1. Beim Fusion-Start, höchstens einmal am Tag, fragt Gridkeeper GitHub nach dem neuesten Release von
   `Eifel-Joe/Gridkeeper`. Nur Tags `gridkeeper-vX.Y.Z`; Original-Tags `vX.Y.Z.W` nie berücksichtigen. Vergleich mit
   der Manifest-Version.
2. Ist eines neuer: Meldung mit Version, Kurzinfo und **Link zu den Versionshinweisen** (Release-Seite), Knopf
   „Jetzt aktualisieren“.
3. „Jetzt aktualisieren“ lädt die Release-ZIP, ersetzt den Add-in-Ordner sicher (erst entpacken und prüfen, dann
   tauschen, Rückweg bei Fehler) und bittet um einen Fusion-Neustart.
4. Installation aus einem Git-Checkout (`.git` vorhanden) wird NIE überschrieben, dort nur Hinweis.
5. In den Einstellungen abschaltbar; ohne Netz keine Prüfung, Fehler still loggen, Fusion-Start nie blockieren.
6. Keine personenbezogenen Daten senden; neutraler User-Agent.

## Entscheidungen

### Prüfen
1. **[Vorschlag] Quelle:** `GET https://api.github.com/repos/Eifel-Joe/Gridkeeper/releases?per_page=30`, ohne
   Anmeldung. Berücksichtigt werden nur Releases, die nicht `draft` und nicht `prerelease` sind und deren Tag genau
   `^gridkeeper-v(\d+)\.(\d+)\.(\d+)$` ist. Das größte (numerisch, nicht als Text) gewinnt. Es braucht ein Asset
   `Gridkeeper-vX.Y.Z.zip`; fehlt es, gibt es nur den Hinweis mit Link, ohne Knopf.
2. **[Vorschlag] „Neuer“:** numerischer Vergleich `(X, Y, Z)` gegen die Manifest-Version. Ist die Manifest-Version
   nicht als `X.Y.Z` lesbar, wird nicht gemeldet (geloggt).
3. **[Vorschlag] Einmal am Tag:** nach Kalendertag (lokal). Gespeichert wird der Tag des letzten *Versuchs*, auch
   eines gescheiterten, damit ein Rechner ohne Netz nicht bei jedem Start wartet. „Später“ heißt: am nächsten Tag
   wieder melden. Kein „Diese Version überspringen“ (nicht verlangt).
4. **[Nutzer/Vorschlag] Nie blockieren:** die Abfrage läuft in einem Hintergrund-Thread (Zeitlimit 10 s je Anfrage),
   das Ergebnis kommt über ein Fusion-Custom-Event in den Haupt-Thread. Fehler (kein Netz, Zeitlimit, HTTP-Fehler,
   kaputtes JSON) landen nur in `futil.log`, keine Meldung.
5. **[Nutzer/Vorschlag] Datenschutz:** gesendet wird nur die Anfrage selbst mit `User-Agent: Gridkeeper-update-check`
   und `Accept: application/vnd.github+json`; keine Version, keine Kennung, kein Cookie. GitHub sieht wie bei jedem
   Seitenaufruf die IP-Adresse; das steht in der Doku.

### Meldung
6. **[Vorschlag] Form:** ein eigener Fusion-Dialog „Gridkeeper update“ (Command mit Eingaben, wie die anderen
   Dialoge), kein `messageBox`, weil der keine Links und keine eigenen Knopftexte kann. Inhalt:
   „Gridkeeper X.Y.Z is available (you have A.B.C).“, die Kurzinfo, der Link „Release notes“ auf die Release-Seite
   (`html_url`), OK-Knopf „Update now“, Abbrechen-Knopf „Later“, Haken „Check for updates at startup“.
   Oberfläche Englisch wie der Rest.
7. **[Vorschlag] Kurzinfo:** der erste Absatz des Release-Texts als Klartext (Markdown-Links → Linktext, `**` weg),
   höchstens 300 Zeichen, sonst mit „…“ gekürzt.
8. **[Vorschlag] Link:** im Text als `<a href>`. Ob Fusion den Link im Dialog öffnet, prüft der Fusion-Test; tut es
   das nicht, ersetzt ein Knopf „Release notes“ (`webbrowser.open`) den Link.
9. **[Vorschlag] Zeitpunkt:** der Dialog erscheint nur, wenn gerade kein anderer Befehl läuft; sonst wird alle 30 s
   erneut versucht (höchstens 10-mal, danach am nächsten Tag).
10. **[Nutzer] Git-Checkout:** derselbe Dialog ohne „Update now“, Text „This add-in runs from a git checkout, update it
    with git.“ plus Link.

### Aktualisieren
11. **[Vorschlag] Ablauf** (alles im Ordner neben dem Add-in, damit Umbenennen auf demselben Laufwerk bleibt;
    Arbeitsordner `<Elternordner>/.gridkeeper-update/`):
    1. ZIP herunterladen (Zeitlimit 60 s, höchstens 50 MB) in den Arbeitsordner.
    2. Prüfen: SHA-256 gleich dem `digest` der API (fehlt der Digest: nur weiter, wenn die Größe stimmt — [Vorschlag]);
       ZIP lesbar; alle Einträge unter genau einem Ordner `Gridkeeper/`, keine absoluten Pfade, kein `..`;
       entpackt höchstens 200 MB; `Gridkeeper/Gridkeeper.manifest` vorhanden mit `version` = X.Y.Z;
       `Gridkeeper/Gridkeeper.py` vorhanden.
    3. Entpacken nach `.gridkeeper-update/new/Gridkeeper`.
    4. **Mitnehmen** aus dem alten Ordner: jede Datei, die die neue ZIP nicht enthält, außer `__pycache__`,
       `*.py`/`*.pyc` und dem Manifest. Das deckt `commandConfig/`, die Update-Einstellungen und eigene Symbole ab,
       ohne Liste, die bei neuen Ordnern veraltet.
    5. Tausch: alter Ordner → `.gridkeeper-update/backup-<Zeitstempel>/Gridkeeper`, neuer Ordner → alter Pfad
       (zwei Umbenennungen). Scheitert die zweite, wird die erste rückgängig gemacht.
    6. Scheitert schon die erste Umbenennung (Windows: Datei im Ordner offen): **Rückfall** auf Kopieren über den
       alten Ordner, vorher vollständige Sicherungskopie nach `backup-<Zeitstempel>`; bricht das Kopieren ab, wird der
       alte Stand aus der Sicherung zurückgeschrieben.
    7. Erfolg: Meldung „Gridkeeper X.Y.Z is installed. Restart Fusion to load it.“ Fehler: Meldung mit Grund, der alte
       Stand bleibt bzw. ist wiederhergestellt.
    8. Aufräumen: `new/` und die ZIP sofort; Sicherungen beim nächsten Start bis auf die jüngste löschen.
12. **[Nutzer] Git-Checkout-Sperre doppelt:** der Installer selbst verweigert, wenn im Ziel `.git` existiert (Datei
    oder Ordner), unabhängig vom Dialog.
13. **[Vorschlag] Kein Neustart durch das Add-in:** Fusion lässt sich nicht sauber selbst neu starten; die Meldung
    bittet darum. Bis zum Neustart läuft die alte Version weiter (Module sind geladen).

### Abschalten
14. **[Vorschlag] Wo:** ein neuer Befehl „Gridkeeper updates“ unter **Utilities › Add-Ins** (nicht in Solid ›
    Create, dort stehen die Erzeuger). Sein Dialog zeigt die installierte Version, den Haken „Check for updates at
    startup“ und einen Knopf „Check now“ (prüft sofort, ohne Tagesgrenze, meldet auch „You have the newest version.“
    und Fehler sichtbar). Derselbe Haken steht im Update-Dialog.
15. **[Vorschlag] Speicherort:** `<Add-in-Ordner>/updateConfig/update.json` mit `{"checkAtStartup": true,
    "lastCheck": "YYYY-MM-DD"}`, wie die übrigen Vorgaben im Add-in-Ordner; wird beim Update mitgenommen (11.4) und
    in `.gitignore` aufgenommen. Fehlt oder ist kaputt: Prüfen an.

### Aufbau
16. **[Vorschlag] Module:**
    - `lib/updateCheck.py` — ohne Fusion: Versions- und Tag-Logik, Auswahl des neuesten Release, Kurzinfo,
      Tagesgrenze, Einstellungsdatei, Git-Erkennung, Abruf mit austauschbarem `urlopen`.
    - `lib/updateInstall.py` — ohne Fusion: Download, Prüfung, Entpacken, Mitnehmen, Tausch mit Rückweg, Aufräumen;
      Dateisystem-Funktionen für Fehlertests austauschbar.
    - `commands/commandUpdates/entry.py` — Fusion: Start-Hook, Thread, Custom Event, die zwei Dialoge.
17. **[Vorschlag] Begleitfund, nicht in dieser Runde:** `config.DEV_TOOLS` übersieht Git-Worktrees (`.git` ist dort
    eine Datei). Kommt als neuer Punkt auf die Liste.

## Nicht dabei
- Automatisches Update ohne Rückfrage, Vorabversionen, Herunterstufen, „Version überspringen“.
- Fusion-Neustart durch das Add-in.
- Update aus dem Git-Checkout heraus (`git pull`).
- Änderung von `release.yml` oder der Manifest-Version; neue Releases/Tags.
- Signaturprüfung über den GitHub-Digest hinaus.

## Ende-zu-Ende-Kriterium
- pytest grün, darin: Versionsvergleich, Tag-Filter (`v2.4.2.0`, Entwürfe, Vorabversionen, fehlendes Asset),
  Kurzinfo, Tagesgrenze, Git-Erkennung (Ordner und Datei), ZIP-Prüfung (falscher Hash, `..`-Pfad, zweiter
  Ordner, falsche Manifest-Version), Tausch mit Mitnehmen, Rückweg bei Fehler in jeder Tauschstufe, Rückfall
  Kopieren, Weigerung bei `.git`. `mkdocs build --strict` grün.
- Fusion-Job 1: Fusions Python ruft die echte API ab (SSL geht), liefert 1.0.0, „nicht neuer“ gegen 1.0.0; lädt die
  echte `Gridkeeper-v1.0.0.zip` und prüft deren Digest.
- Fusion-Job 2: Hintergrund-Thread mit gefälschter Release-Liste (lokale Datei, Version 9.9.9, ZIP aus dem
  Worktree gebaut wie `release.yml`) → Custom Event kommt im Haupt-Thread an; Installer tauscht in einen
  Testordner unter dem Scratch-Verzeichnis, `commandConfig` ist mitgenommen.
- Handtest (Hauptsitzung/Nutzer): Dialog sehen, Link öffnet die Release-Seite, „Update now“ auf einer Test-Installation
  (Kopie der 1.0.0-ZIP, Manifest auf 0.9.0 gesetzt) ersetzt sie, nach Neustart zeigt Fusion 1.0.0. Damit ist kein
  Test-Release auf GitHub nötig; der Weg über ein echtes neues Release läuft erst mit 1.1.0.
