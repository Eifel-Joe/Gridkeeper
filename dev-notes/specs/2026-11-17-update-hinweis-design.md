# Runde Update-Hinweis: Gridkeeper prüft selbst auf neue Versionen (p310)

Stand 17.11.2026, Entwurf zur Freigabe durch die Hauptsitzung. Branch `claude/update-hinweis-6b49ec` von `master`
(0b0550a). Kommt ins Release 1.1.0; die Manifest-Version ändert diese Runde nicht.

Markierung: **[Vorgabe]** = Vorgabe wörtlich oder aus dem Auftrag, **[Vorschlag]** = meine Festlegung, die die
Hauptsitzung freigeben oder ändern soll.

## Punkt und Wortlaut

p310 „Add-in prüft selbst auf neue Gridkeeper-Versionen“.
Vorgabe: Für Updates Variante 2; beim Update-Hinweis auch einen Link zu den Versionshinweisen einbauen, damit
man weiß, was man bekommt.

## Warum

Gridkeeper kommt nicht über den App Store; wer die Release-ZIP installiert hat, erfährt von neuen Versionen nur, wenn
er auf GitHub nachsieht. Das Update von Hand (ZIP über den Ordner entpacken) ist fehleranfällig. Ein Entwickler arbeitet
aus einem Git-Checkout, der darf nie angefasst werden.

## Was es heute gibt (Befund)

- Kein Update-Code, kein Netzzugriff im Add-in. `Gridkeeper.py` ruft nur `commands.start()`.
- Manifest-Version `1.0.0`, Release `gridkeeper-v1.0.0` mit Asset `Gridkeeper-v1.0.0.zip`; die GitHub-API liefert je
  Asset ein `digest` (`sha256:…`). Die ZIP enthält genau einen Ordner `Gridkeeper/` (siehe `release.yml`).
- **Gespeicherte Dialog-Vorgaben liegen im Add-in-Ordner** (`commands/*/commandConfig/`), ebenso dürfen Nutzer eigene
  SVG-Symbole in die Symbolordner legen (Doku Symbols). Ein Ordnertausch muss beides mitnehmen.
- Es gibt keinen globalen Einstellungsdialog; „Gridkeeper settings“ zeigt nur die Einstellungen eines Körpers.
- `config.DEV_TOOLS` erkennt den Git-Checkout per `os.path.isdir('.git')`; in einem Git-Worktree ist `.git` eine Datei.

## Anforderungen (Variante 2) [Vorgabe]

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
4. **[Vorgabe/Vorschlag] Nie blockieren:** die Abfrage läuft in einem Hintergrund-Thread (Zeitlimit 10 s je Anfrage),
   das Ergebnis kommt über ein Fusion-Custom-Event in den Haupt-Thread. Fehler (kein Netz, Zeitlimit, HTTP-Fehler,
   kaputtes JSON) landen nur in `futil.log`, keine Meldung.
5. **[Vorgabe/Vorschlag] Datenschutz:** gesendet wird nur die Anfrage selbst mit `User-Agent: Gridkeeper-update-check`
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
10. **[Vorgabe] Git-Checkout:** derselbe Dialog ohne „Update now“, Text „This add-in runs from a git checkout, update it
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
12. **[Vorgabe] Git-Checkout-Sperre doppelt:** der Installer selbst verweigert, wenn im Ziel `.git` existiert (Datei
    oder Ordner), unabhängig vom Dialog.
13. **[Vorgabe] Neu laden nach dem Update — messen, nicht annehmen.** Vorgabe: Nach einem Update muss
    zumindest das Plugin neu geladen oder Fusion neu gestartet werden; zu testen ist, was
    notwendig ist und was funktioniert. Der Fehler vom 14.11. könnte auch eine andere Ursache gehabt haben.
    Bis zum Neu-Laden läuft die alte Version weiter (Module sind geladen). Zu prüfende Wege, jeder unvoreingenommen:
    - **W1 Fusion-Neustart.**
    - **W2 Skripte und Add-ins:** Gridkeeper stoppen, dann ausführen (von Hand).
    - **W3 Fusion-API:** Add-in stoppen/starten über die Add-in-Objekte der API, falls Fusion sie anbietet
      (vorhandene Eigenschaften und Methoden misst Job 3, nicht aus dem Gedächtnis), aus einem Skript und aus dem
      Add-in selbst (verzögert über Custom Event, da ein Add-in sich nicht im eigenen Handler beenden sollte).
    - **W4 Neu-Laden aus dem Add-in:** `stop()`, Module des Pakets aus `sys.modules` entfernen, neu ausführen,
      `run()` — wie `fusion-addin-reload.py`. Der Befund vom 14.11. (danach öffneten sich die Menübefehle nicht
      mehr) gilt nur als Hinweis, die Ursache ist offen.
    **Prüfung je Weg:** danach alle Befehle öffnen — Gridkeeper bin, baseplate, label, box, Export, Rechtsklick
    settings/rebuild/clone — und die laufende Version prüfen (E13a). **Das Ergebnis bestimmt die Meldung:** gibt es
    einen sicheren Weg ohne Neustart, bekommt die Erfolgsmeldung einen Knopf dafür (W3/W4) bzw. die Anleitung (W2);
    sonst bittet sie um den Fusion-Neustart. Ein Fusion-Neustart durch das Add-in selbst ist nicht vorgesehen.
13a. **[Vorschlag] Laufende Version sichtbar:** beim Start merkt sich das Add-in die Manifest-Version im Speicher.
    Der Dialog „Gridkeeper updates“ zeigt „Running X, installed Y“; weichen sie ab, steht dort „Restart Fusion (or
    reload Gridkeeper) to use Y“. Damit ist die laufende Version im Test und für Nutzer prüfbar, ohne dem Manifest
    auf der Platte zu glauben.

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
- Fusion-Neustart durch das Add-in (Neu-Laden des Add-ins nur, wenn die Matrix E13 einen sicheren Weg belegt).
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
- Neu-Laden-Matrix (E13): je Weg W1–W4 ein Durchgang auf einer Test-Installation (aus dem Worktree gebaut,
  Version 9.9.8 → per Installer 9.9.9 mit sichtbarer Markierung); Ergebnis je Weg: laufende Version, jeder der
  acht Befehle öffnet/öffnet nicht, Fehler im Textbefehlsfenster. Git-Checkout-Add-in muss währenddessen
  gestoppt sein (gleiche Befehls-IDs) und wird danach wieder gestartet; das braucht die Hauptsitzung bzw. den Nutzer.
  Das Ergebnis kommt als Tabelle in die Spec und bestimmt die Erfolgsmeldung.
- Handtest (Hauptsitzung): Dialog sehen, Link öffnet die Release-Seite, „Update now“ auf einer Test-Installation
  (aus diesem Branch gebaut mit Version 0.9.0, `dev-notes/tools/update-fusion-jobs/build_test_install.py`; die
  1.0.0-ZIP selbst hat den Update-Code nicht) ersetzt sie durch das echte 1.0.0, nach Neustart zeigt Fusion 1.0.0. Damit ist kein
  Test-Release auf GitHub nötig; der Weg über ein echtes neues Release läuft erst mit 1.1.0.

## Umsetzungsnotizen (Runde Update-Hinweis, 17.11.2026)
- E6 und E14 sind ein Befehl: „Gridkeeper updates“. Vom Start-Check geöffnet hat er OK = „Update now“ und
  Abbrechen = „Later“ wie E6; aus dem Menü geöffnet „Close“, die Version (E13a), „Check now“ und den Haken (E14).
  Findet „Check now“ ein Release, erscheint im Dialog ein Knopf „Update now“.
- E8: Link im Text **und** ein Knopf „Release notes“, bis der Handtest zeigt, ob Fusion den Link im Text öffnet.
- E11.7: Erfolgsmeldung „Gridkeeper X.Y.Z is installed. Restart Fusion to load it, until then the old version runs.“
  (Review: bis zum Neustart läuft alter Code gegen neue Dateien, die Meldung soll nicht zum Weiterarbeiten einladen).
- Kurzinfo (E7): Überschriftszeilen fallen weg, nicht der Absatz darunter.
- Seiten-Link und Download nur, wenn die Adresse mit `https://github.com/` beginnt; API-Antwort höchstens 5 MB.
- E11.6 Rückfall Kopieren: ob der alte Stand zurück ist, entscheidet der Inhaltsvergleich mit der Sicherung (eine
  gesperrte Datei scheitert in beide Richtungen, hat aber den alten Inhalt). E11.8: das Aufräumen beim Start löscht
  nur ältere Sicherungen, `new/` und die ZIP räumt `install` selbst; beide teilen eine Sperre.
- Mitnehmen (E11.4) vergleicht Pfade ohne Groß-/Kleinschreibung (Windows). Nebenwirkung, von der Hauptsitzung
  akzeptiert: Bilder/SVGs, die eine neue Version absichtlich entfernt, bleiben aus der alten erhalten (Doku nennt es).

## Messung Neu-Laden (E13), 17.11.2026, Fusion 2706.1.17
Durchgeführt von der Klicktest-Sitzung nach `update-hinweis-neuladen-matrix.md` (Notizordner), Test-Add-in 9.9.8 →
Installer 9.9.9 (`renamed`). Vor dem Neu-Laden zeigte der Dialog in allen Wegen „Running 9.9.8, installed 9.9.9“.

| Prüfung | W1 Fusion-Neustart | W2 Stop/Run im Dialog | W3 API Script.stop/run (Skript) | W4 Module neu laden |
|---|---|---|---|---|
| Läuft 9.9.9 | ja | ja | ja | (Job meldet 9.9.9) |
| Bin, Baseplate, Label, Box öffnen | ja | ja | ja | **nein**, kein Dialog öffnet sich, kein Fehler im Log |
| Rechtsklick settings/rebuild/clone, export | ja | ja | ja | nicht prüfbar |
| Befehle nur einmal | ja | ja | ja | ja |

**Folge für die Meldung:** Erfolgsmeldung und Versionszeile nennen Fusion-Neustart und Stop/Run in Scripts and
Add-Ins (W1/W2). Kein Knopf: W4 ist kaputt (bestätigt die Beobachtung vom 14.11.), W3 ist nur aus einem Skript
gemessen; aus dem Add-in selbst müsste der Code, der entladen wird, das Add-in wieder starten — nicht gebaut.
Nebenbefund für die Projektarbeit: W3 (`app.scripts` → `Script.stop()`/`run()`) taugt als Ersatz für
`fusion-addin-reload.py`, das die Befehle tot zurücklässt.

## Messung Selbst-Neustart (Runde 33, p321), 18.11.2026, Fusion 2706.1.17
Offen war W3 **aus dem Add-in selbst**. Gemessen auf einer Testkopie in Fusions AddIns-Ordner (Manifest 9.9.1, Git-Add-in
währenddessen gestoppt), Werkzeug `dev-notes/tools/r33-self-restart/`. Eine Sonde nur in der Kopie: ein Custom-Event-
Handler im Add-in sucht sein eigenes `Script` (über `folder`) und ruft `stop()`, dann `run()`. Vor dem Auslösen wurde das
Manifest der Kopie auf 9.9.2 gesetzt (simuliertes Update).

| Prüfung | Ergebnis |
|---|---|
| `stop()` / `run()` aus dem eigenen Handler | beide `True`, keine Ausnahme |
| Neuer Start | ja, 1 s später: Manifest 9.9.2, neues Modulobjekt, `runningVersion (9, 9, 2)` |
| Updates, Bin, Baseplate, Label, Box öffnen (execute → `activeCommand`) | alle fünf aktiv, Dialoge bauen ihre Eingaben auf |

Eigenheiten: `fireCustomEvent` aus einem Skript gab `False` zurück, der Handler lief trotzdem. `Script.isRunning` und
`Script.version` zeigen direkt nach `run()` noch den alten Stand. `unlink()` geht für Add-ins im Standard-AddIns-Ordner
nicht („script is not linked“). **Folge:** Der Selbst-Neustart aus dem Add-in geht; ein Knopf „Reload Gridkeeper“ ist
machbar (Spec-Ergänzung `2026-11-18-runde-33-design.md`).

**Produkt-Test Reload Gridkeeper (Runde 33, 18.11.2026):** Testkopie ohne Sonde (9.9.1), Manifest auf 9.9.2, Gridkeepers
eigenes Event `EifelJoe_Gridkeeper_reload` gefeuert: danach läuft das Paket der Kopie mit `runningVersion (9, 9, 2)`,
Updates, Bin, Baseplate, Label und Box öffnen sich. Git-Add-in danach wieder gestartet (1.1.0), Kopie entfernt.
