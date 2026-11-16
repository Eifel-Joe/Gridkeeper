# Runde 24 – README und Doku für Gridkeeper (p231, p230, p237)

Branch `runde-24` im Worktree `wt-doku`, von master fce1f12. Kein Push, kein Merge, keine Tags.

## Plan

1. Interne Notizen aus `docs/` holen: `docs/specs` → `dev-notes/specs`, `docs/plans` → `dev-notes/plans` (git mv),
   Verweise in Tests und e2e-Skripten angepasst. `docs/` gehört danach allein der Website.
2. MkDocs-Material-Gerüst: `mkdocs.yml` (wie SpoolmanScale-Docs, ohne i18n), `.github/workflows/pages.yml` mit
   `mkdocs build --strict` (wirkt erst nach des Nutzers Freigabe, Pages muss im Repo eingeschaltet werden).
3. Bilder: die Original-Bilder `documentation/assets` nach `docs/assets` verschoben (MkDocs liest nur `docs/`), noch
   passende davon eingebunden. Neue Bilder als Platzhalter `docs/assets/images/<name>.png` (graue Platzhalter-PNG, damit
   `--strict` baut), Liste in `docs/assets/images/NEEDED.md`.
4. Seiten (nur Englisch), Befehlsnamen schon „Gridkeeper …“ (Runde 23), Dialogfelder wie im Code:
   Home, Installation, What's new, Baseplates, Bins (Größe, Körper, Fächer, Scoop, Label-Tab, Basis), Labels und
   Farben/Mehrfarbdruck, Cullenect-Taschen und Einleger mit Symbolen, Settings/Rebuild/Clone, Speichern/Laden,
   Parameter, Known deviations (p237), Snapshot-Tests für Entwickler, Credits und Lizenz.
5. README neu: Gridkeeper, „our further development of GridfinityGenerator“, vibe-coded, nur ZIP aus den
   GitHub-Releases, Credits, Lizenz, Link auf die Doku (Platzhalter-Adresse).
6. `mkdocs build --strict` und `python -m pytest -q` grün, Review per Opus-Subagent (Inhalt gegen Code), Funde einarbeiten.

Commits je Teil.

## Offen / für die Hauptsitzung

- Die Projekt-`CLAUDE.md` (außerhalb des Forks) nennt die Spec noch unter `FusionGridfinityGenerator/docs/specs/…`,
  nach dem Merge heißt der Pfad `dev-notes/specs/…`.
- Doku-Adresse ist ein Platzhalter (`https://eifel-joe.github.io/Gridkeeper/`), Repo wird noch umbenannt.
