# Update-Hinweis (p310) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans (native, diese Sitzung), TDD je Task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Gridkeeper prüft einmal am Tag im Hintergrund auf ein neueres `gridkeeper-vX.Y.Z`-Release, zeigt Version,
Kurzinfo und Link zu den Versionshinweisen und ersetzt auf Wunsch den Add-in-Ordner sicher (nie einen Git-Checkout).

**Architecture:** Zwei Fusion-freie Module (`lib/updateCheck.py` Abfrage/Logik, `lib/updateInstall.py`
Download/Prüfung/Tausch) mit pytest; ein Fusion-Befehl `commands/commandUpdates` verbindet Start-Hook, Thread,
Custom Event und Dialoge. Nur Standardbibliothek (`urllib`, `zipfile`, `hashlib`, `shutil`, `threading`).

**Tech Stack:** Python 3.12+ (Fusion), pytest mit `tests/stubs`, mkdocs.

**Spec:** `dev-notes/specs/2026-11-17-update-hinweis-design.md` (Nummern E1–E17 = dortige Entscheidungen).

## Global Constraints
- Repo `Eifel-Joe/Gridkeeper`; Tag-Regex `^gridkeeper-v(\d+)\.(\d+)\.(\d+)$`; Asset `Gridkeeper-vX.Y.Z.zip`.
- User-Agent `Gridkeeper-update-check`, nichts sonst Persönliches; Zeitlimit Abfrage 10 s, Download 60 s.
- ZIP ≤ 50 MB, entpackt ≤ 200 MB, genau ein Ordner `Gridkeeper/`.
- Einstellungen `updateConfig/update.json` `{"checkAtStartup": bool, "lastCheck": "YYYY-MM-DD"}`, Vorgabe an.
- Arbeitsordner `<Eltern>/.gridkeeper-update/` (`new/`, `backup-<YYYYmmdd-HHMMSS>/`).
- Oberfläche Englisch; Manifest-Version bleibt 1.0.0; Längen-/Fusion-Regeln der Projekt-CLAUDE.md unberührt.

## Review Focus
1. Netz fehlt/hängt beim Start → Fusion startet normal, kein Fenster, ein Logeintrag (Task 2: `fetchReleases` mit werfendem/zeitlimit-`urlopen` → `None`; Task 6 Fusion-Job).
2. Windows hält eine Datei im Add-in-Ordner offen → Rückfall Kopieren, bei Abbruch alter Stand vollständig zurück (Task 4 Tests mit injizierten Fehlern).
3. Nutzer hat eigene SVG-Symbole / gespeicherte Vorgaben → nach Update noch da (Task 4 `test_carries_user_files`).
4. Installation liegt in einem Git-Worktree (`.git` ist Datei) → nie überschrieben (Task 1 + Task 4 `test_refuses_git_file`).
5. Release-Text leer, ohne Absatz oder sehr lang → Kurzinfo leer bzw. 300 Zeichen mit „…“, kein Absturz (Task 1).

---

### Task 1: Versions- und Release-Logik (`lib/updateCheck.py`, ohne Netz)

**Files:** Create `lib/updateCheck.py`; Test `tests/test_update_check.py`

**Interfaces – Produces:**
- `parseVersion(text: str) -> tuple[int, int, int] | None` (`'1.0.0'` → `(1,0,0)`; `'1.0'`, `'v1.0.0'`, `''` → None)
- `tagVersion(tag: str) -> tuple[int,int,int] | None` (nur Regex oben; `v2.4.2.0`, `gridkeeper-v1.0`, `gridkeeper-v1.0.0-beta` → None)
- `@dataclass(frozen=True) Release(version: tuple, tag: str, pageUrl: str, summary: str, assetUrl: str | None, assetSize: int | None, assetDigest: str | None)`; `Release.versionText -> str`
- `newestRelease(releases: list[dict], current: tuple) -> Release | None` (nur neuer als `current`; ohne `draft`/`prerelease`; Asset per Name)
- `summary(body: str | None, limit: int = 300) -> str` (erster Absatz, `[t](u)`→`t`, `**`/`__`/`` ` `` weg, `\r\n` normalisiert)
- `isGitCheckout(folder: str) -> bool` (`os.path.exists(join(folder,'.git'))`)
- `readSettings(path) -> dict`, `writeSettings(path, settings) -> bool`, `isDue(settings, today: date) -> bool`, `manifestVersion(addinFolder) -> tuple | None`

- [ ] **Step 1: Tests** — u. a.
  - `test_newest_ignores_original_tags`: Liste mit `v2.4.2.0` (Version höher), `gridkeeper-v1.1.0`, `gridkeeper-v1.0.0` → `.tag == 'gridkeeper-v1.1.0'`
  - `test_numeric_not_text`: `gridkeeper-v1.10.0` schlägt `gridkeeper-v1.9.0`
  - `test_skips_draft_and_prerelease`, `test_none_when_not_newer` (current `(1,1,0)`), `test_missing_asset_keeps_release_without_url` (`assetUrl is None`)
  - `test_summary_first_paragraph_plain`: `'The first **Gridkeeper**, see [docs](https://x).\r\n\r\nMore'` → `'The first Gridkeeper, see docs.'`; `test_summary_cut` (400 Zeichen → Länge 300, endet `…`); `test_summary_empty` (`None` → `''`)
  - `test_git_dir_and_file` (Ordner `.git` und Datei `.git` → True, keins → False)
  - `test_due_once_a_day`: `{'lastCheck':'2026-11-17'}` + 17.11. → False, + 18.11. → True; `{}` → True; `checkAtStartup False` → False
  - `test_settings_broken_file_defaults` (Müll in Datei → `{'checkAtStartup': True}`)
  - `test_manifest_version` (Manifest-JSON mit Tab-Einrückung wie im Repo → `(1,0,0)`)
- [ ] **Step 2:** `python -m pytest tests/test_update_check.py` → FAIL (Modul fehlt)
- [ ] **Step 3:** Implementieren
- [ ] **Step 4:** PASS, dann volle Suite `python -m pytest` grün
- [ ] **Step 5:** Commit „Update-Prüfung: Versions-, Tag- und Release-Logik (p310)“

### Task 2: Abruf (`fetchReleases`, `checkForUpdate`)

**Files:** Modify `lib/updateCheck.py`; Test `tests/test_update_check.py`

**Interfaces – Produces:**
- `API_URL = 'https://api.github.com/repos/Eifel-Joe/Gridkeeper/releases?per_page=30'`, `USER_AGENT = 'Gridkeeper-update-check'`
- `fetchReleases(url=API_URL, urlopen=urllib.request.urlopen, log=print) -> list[dict] | None` (Fehler → None + log)
- `checkForUpdate(addinFolder: str, fetch=fetchReleases, log=print) -> Release | None`

- [ ] **Step 1: Tests** — `test_request_headers_only_neutral` (Fake-`urlopen` fängt `Request`: Header genau `User-agent`, `Accept`; Zeitlimit 10), `test_fetch_errors_are_none` (URLError, `socket.timeout`, HTTP 403, kaputtes JSON, JSON-Objekt statt Liste → None, je ein Log), `test_check_for_update` (Fake-Fetch + Manifest 1.0.0 → Release 1.1.0), `test_check_unreadable_manifest_none`
- [ ] **Step 2–4:** RED → implementieren → GREEN, volle Suite
- [ ] **Step 5:** Commit „Update-Prüfung: Abruf bei GitHub mit neutralem User-Agent (p310)“

### Task 3: ZIP laden und prüfen (`lib/updateInstall.py`)

**Files:** Create `lib/updateInstall.py`; Test `tests/test_update_install.py` (ZIPs im `tmp_path` gebaut, Hilfsfunktion `makeZip(entries: dict[str, bytes])`)

**Interfaces – Produces:**
- `class UpdateError(Exception)` (Text = Grund für die Meldung)
- `download(url, target, expectedSize, urlopen=..., limit=50*2**20) -> str`
- `verifyZip(zipPath, version: tuple, digest: str | None, size: int | None) -> None` (wirft `UpdateError`)
- `extract(zipPath, targetParent) -> str` (Pfad des entpackten `Gridkeeper`)

- [ ] **Step 1: Tests** — `test_verify_ok`, `test_wrong_digest`, `test_no_digest_size_must_match`, `test_rejects_dotdot` (`Gridkeeper/../x`), `test_rejects_absolute`, `test_rejects_second_top_folder`, `test_rejects_wrong_manifest_version`, `test_rejects_missing_py`, `test_rejects_too_big_uncompressed` (Limit per Parameter klein gesetzt), `test_download_stops_over_limit`
- [ ] **Step 2–4:** RED → implementieren → GREEN
- [ ] **Step 5:** Commit „Update: Release-ZIP laden und prüfen (p310)“

### Task 4: Tausch mit Mitnehmen und Rückweg

**Files:** Modify `lib/updateInstall.py`; Test `tests/test_update_install.py`

**Interfaces – Produces:**
- `carryOver(oldFolder, newFolder) -> list[str]` (E11.4: Dateien, die `new` nicht hat, ohne `__pycache__`, `*.py`, `*.pyc`, `*.manifest`)
- `swap(addinFolder, newFolder, backupFolder, rename=os.replace, copytree=shutil.copytree, rmtree=shutil.rmtree) -> str` (`'renamed'` oder `'copied'`; wirft `UpdateError` nach Wiederherstellung)
- `install(release: Release, addinFolder, urlopen=..., now=datetime.now) -> None` (Ablauf E11.1–E11.8; Weigerung bei `isGitCheckout`)
- `cleanupBackups(addinFolder) -> None` (alle bis auf die jüngste Sicherung, `new/`, ZIPs)

- [ ] **Step 1: Tests** — `test_swap_renames` (Ergebnis Inhalt neu, Sicherung = alt); `test_second_rename_fails_restores` (zweites `rename` wirft → alter Ordner wieder am Platz, `UpdateError`); `test_first_rename_fails_copies` (erstes wirft `PermissionError` → `'copied'`, Inhalt neu, Sicherung vollständig); `test_copy_fails_restores` (Kopieren wirft mittendrin → Inhalt wieder alt); `test_carries_user_files` (`commands/commandCreateBin/commandConfig/x.json`, eigenes `lib/…/hardware/my.svg`, `updateConfig/update.json` mitgenommen; altes `lib/gone.py` und `__pycache__` nicht); `test_refuses_git_dir`, `test_refuses_git_file` (Ordner bleibt unverändert); `test_install_end_to_end` (Fake-`urlopen` liefert ZIP, Release mit Digest → neuer Inhalt, `new/` weg); `test_cleanup_keeps_newest_backup`
- [ ] **Step 2–4:** RED → implementieren → GREEN, volle Suite
- [ ] **Step 5:** Commit „Update: Add-in-Ordner sicher tauschen, Vorgaben mitnehmen (p310)“

### Task 5: Fusion-Befehl `commandUpdates`

**Files:** Create `commands/commandUpdates/entry.py`, `__init__.py`, `resources/` (Icon 16/32/64, aus vorhandenem Icon abgeleitet); Modify `commands/__init__.py` (in `commands` aufnehmen), `.gitignore` (`updateConfig`); Test `tests/test_update_command.py` (nur Fusion-freie Teile)

**Interfaces – Consumes:** Task 1–4. **Produces:**
- `dialogHtml(release: Release, current: tuple, gitCheckout: bool) -> str` (Fusion-frei, getestet: enthält `versionText`, `A.B.C`, `<a href="{pageUrl}">Release notes</a>`, escapte Kurzinfo; bei `gitCheckout` den Git-Satz aus E10)
- `start()`/`stop()`: Befehl „Gridkeeper updates“ in Utilities › Add-Ins (`SolidScriptsAddinsPanel` bzw. Panel-ID im Fusion-Job prüfen), Custom Event registrieren; `checkAtStartup` + `isDue` → `lastCheck` setzen, Daemon-Thread `checkForUpdate` → `app.fireCustomEvent(EVENT_ID, json)`; Handler zeigt Update-Dialog, wenn `ui.activeCommand == 'SelectCommand'`, sonst bis 10 × 30 s neu (Timer-Thread + Event); `stop()` unregistert Event.
- Update-Dialog (E6): Textbox HTML, Haken „Check for updates at startup“, OK „Update now“ (ausgeblendet ohne Asset oder bei Git), Cancel „Later“; OK → `install` (im Haupt-Thread mit Fortschrittsdialog `ui.createProgressDialog`), danach `messageBox` E11.7.
- `RUNNING_VERSION` wird in `start()` einmal aus dem Manifest gelesen (E13a); Fusion-frei getestet:
  `versionLine(running, installed) -> str` (`'Running 1.0.0'` bzw. `'Running 1.0.0, installed 1.1.0. Restart Fusion (or reload Gridkeeper) to use 1.1.0.'`).
- Befehls-Dialog (E14): `versionLine`, Haken, Knopf „Check now“ (ohne Tagesgrenze, zeigt auch „newest“ und Fehler).
- `run()` in `Gridkeeper.py` unverändert; `cleanupBackups` beim Start im Thread.

- [ ] **Step 1:** Tests `dialogHtml` (drei Fälle, inkl. `<script>` in der Kurzinfo escaped) → RED
- [ ] **Step 2:** implementieren → GREEN, volle Suite
- [ ] **Step 3:** Commit „Update-Hinweis: Befehl, Hintergrundprüfung und Dialoge (p310)“

### Task 6: Fusion-Jobs (über die Hauptsitzung)

**Files:** Create `dev-notes/tools/update-fusion-jobs/job1_api.py`, `job2_thread_install.py` (laden die Module aus dem Worktree per `importlib`, schreiben Ergebnis-JSON); Job-Dateien nach `D:\Entwicklung\Gridfinity\fusion-auftraege` (Format der vorhandenen Aufträge), je < 50 s.

- [ ] **Job 1:** echte API → newest 1.0.0, `checkForUpdate` gegen 1.0.0 → None; Download `Gridkeeper-v1.0.0.zip` + `verifyZip` OK; Zeit < 30 s.
- [ ] **Job 2:** Thread mit Fake-Fetch (9.9.9) → Custom Event im Haupt-Thread empfangen (Handler schreibt Datei statt Dialog); `install` aus lokal gebauter ZIP (Bau wie `release.yml`, Manifest 9.9.9) in Testordner im Scratch, `commandConfig` mitgenommen; Panel-ID von Utilities › Add-Ins ausgeben.
- [ ] **Job 3 (API-Erkundung, nur lesen):** listet, was Fusion zu Add-ins anbietet (`dir(app)`, Objekte mit
  „script“/„addin“ im Namen, deren Eigenschaften/Methoden, Eintrag für Gridkeeper mit `isRunning` o. ä.). Ergebnis
  entscheidet, ob W3 überhaupt möglich ist.
- [ ] Jobnamen der Hauptsitzung melden, Ergebnis abwarten, Abweichungen per TDD nachziehen.

### Task 6a: Neu-Laden-Matrix (Spec E13) und Folgen für die Meldung

**Files:** Create `dev-notes/tools/update-fusion-jobs/build_test_install.py` (baut aus dem Worktree eine
Test-Installation wie `release.yml`, Manifest-Version als Parameter, optional Markierung im Befehlsnamen „(9.9.9)“),
`job4_reload_addin.py` (W4: Neu-Laden wie in `fusion-addin-reload.py`, aber für den Test-Pfad), ggf. `job5_api_restart.py` (W3,
nur wenn Job 3 einen Weg zeigt); Ergebnis-Tabelle in die Spec (Abschnitt „Messung Neu-Laden“).

- [ ] Vorbereitung (Hauptsitzung/Nutzer): des Nutzers Gridkeeper stoppen, Test-Installation 9.9.8 hinzufügen und starten.
- [ ] Je Weg W1, W2, W3 (falls möglich), W4, jeweils nach frischem Fusion-Start: Installer setzt 9.9.9 auf die
  Platte (Job), Weg anwenden, dann prüfen: „Gridkeeper updates“ zeigt Running/Installed, Bin, Baseplate, Label,
  Box, Export öffnen und mit Abbrechen schließen, Rechtsklick settings/rebuild/clone auf einem gebauten Teil,
  Textbefehlsfenster auf Fehler. Klicks macht die Hauptsitzung (Testplan-Checkliste von mir).
- [ ] Danach: Test-Installation entfernen, des Nutzers Gridkeeper wieder starten.
- [ ] Auswertung in die Spec; Erfolgsmeldung (Task 5) danach festlegen: Knopf „Reload Gridkeeper“ nur bei
  belegtem sicheren W3/W4, Anleitung bei W2, sonst „Restart Fusion“. Änderung per TDD (Text in `dialogHtml`/
  `successText(reloadWay)` getestet), Commit „Update: Meldung nach Messung Neu-Laden (p310)“.

### Task 7: Doku und Changelog

**Files:** Modify `docs/getting-started/installation.md` (Abschnitt „Update“: automatische Prüfung, Dialog, „Update now“, Git-Checkout, Sicherung in `.gridkeeper-update`, Rückweg von Hand; neuer Abschnitt „Update check and privacy“: was gesendet wird, Abschalten); `docs/getting-started/whats-new.md` (ein Punkt); `CHANGELOG-CULLENECT.md` unter „Unreleased (1.1.0)“ Abschnitt „Update check (p310)“.

- [ ] `mkdocs build --strict` → ohne Warnung; `python -m pytest` grün
- [ ] Commit „Doku: Update-Prüfung und Abschalten (p310)“

### Task 8: Review, PR

- [ ] Opus-Review (`superpowers:requesting-code-review`) über Diff + Spec + Plan; Funde über `receiving-code-review`, je Fund Test + Fix + Commit
- [ ] Neuer Punkt p320 auf der Liste: `config.DEV_TOOLS` übersieht Git-Worktrees
- [ ] Push, PR gegen `master` (Text vorher der Hauptsitzung zeigen), CI pytest 3.13/3.14 grün, PR-Link + Testplan melden
