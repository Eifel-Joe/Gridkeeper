# Snapshot-Tests

Gridkeeper hat zwei Arten von Tests: Unit-Tests, die überall laufen, und Form-Snapshot-Tests, die Modelle in Fusion
bauen und mit aufgezeichneten Snapshots vergleichen.

## Unit-Tests

Die Geometrieberechnung, die Einstellungsdateien, die Layouts und die Dialoglogik sind, wo es geht, frei von Fusion
gehalten und werden mit pytest gegen einen Ersatz der Fusion-API in `tests/stubs` getestet:

```bash
python -m pytest -q
```

## Form-Snapshot-Tests { #shape-snapshot-tests }

Jeder Fall in `tests/e2e/cases/` ist eine JSON-Datei mit den Einstellungen eines Behälters, einer Grundplatte oder
eines Einlegers, die von den Dialogvorgaben in `lib/defaultSettings.py` abweichen, Längen in mm und Winkel in Grad.
Sein Snapshot in `tests/e2e/snapshots/<case>/` enthält die erzeugten Formen, ihre Fingerabdrücke, alle Einstellungen,
mit denen sie gebaut wurden, und ein Vorschaubild. Die Liste der Fälle mit ihren Vorschauen steht in
[tests/e2e/README.md](https://github.com/Eifel-Joe/Gridkeeper/blob/master/tests/e2e/README.md).

### Ausführen { #running-them }

Die Testbefehle gibt es nur, wenn das Zusatzmodul aus einem **Git-Checkout** mit einem Ordner `.git` läuft; Releases
werden ohne ihn und ohne die Befehle ausgeliefert. Ein `git worktree`, in dem `.git` eine Datei ist, erhält sie
ebenfalls nicht.

1. Fügen Sie den Checkout in **Skripte und Zusatzmodule** als Zusatzmodul hinzu, wie in
   [Installation](../getting-started/installation.md).
2. **Dienstprogramme › Zusatzmodule › Gridkeeper tests: run** öffnet den Testbericht und baut jeden Fall in einem
   eigenen Dokument.
3. Der Bericht zeigt jeden Fall als bestanden oder fehlgeschlagen, mit dem, was abweicht: die Anzahl der Körper, ihr
   Volumen, der Quader um sie herum, eine Einstellung, die sich geändert hat. Bei einem fehlgeschlagenen Fall können
   Sie die gebauten Körper gegen den Snapshot ansehen.

**Gridkeeper tests: update snapshots** zeichnet nach einer beabsichtigten Änderung neue Snapshots auf; es zeigt, was es
ersetzen und entfernen wird, bevor es schreibt.

![Die Testpalette nach dem Ausführen eines Falls: Der Fall ist bestanden, sein Dokument bleibt für Diff, Built und Snapshot geöffnet](../assets/images/snapshot-test-report.png)

### Sprache beim Testen { #language-for-testing }

Die Entwicklungsbefehle (*Gridkeeper tests: run*, *Gridkeeper docs: render models*) mit ihren Fenstern und dem Bericht
bleiben im Zusatzmodul englisch. Eine Datei `languageOverride` im Ordner des Zusatzmoduls, mit dem Inhalt `de` oder
`en`, legt die Sprache des Zusatzmoduls zum Testen fest und überstimmt die Sprache von Fusion; sie wird beim Start des
Zusatzmoduls gelesen.

### Was ein Fall prüfen kann { #what-a-case-can-check }

- **Parameter:** Ein Fall kann nach dem Bauen Benutzerparameter setzen; der Lauf vergleicht die neu berechneten Körper
  mit dem Fall, der von Anfang an mit diesen Werten gebaut wurde.
- **Bestimmung der Skizzen:** Jede Skizze, die der Generator anlegt, muss vollständig bestimmt sein; Fälle mit
  Beschriftungen und Cullenect-Fälle schlagen sonst fehl, andere Fälle protokollieren solche Skizzen.
- **Bauteilkonstruktionen:** Ein Fall kann in einer Bauteilkonstruktion gebaut werden (`"designIntent": "part"`).
- **Zoll:** Jeder Fall wird ein zweites Mal in einem Dokument in Zoll gebaut und mit demselben Snapshot verglichen; seine
  Flächen müssen genauso aufgeteilt sein wie in mm. Eine Länge, die Fusion als Zahl statt in mm übergeben wird (siehe
  `dim.lengthInput`), fällt hier auf.
- **Beschriftungen:** Behälter mit Beschriftungstext werden nach ihrer Form verglichen, nicht danach, wo jeder
  Buchstabe liegt, was von der Schriftart und der Fusion-Version abhängt. Eingefärbte Fälle prüfen das Aussehen ihrer
  Körper.

### Einen Fall hinzufügen { #adding-a-case }

Schreiben Sie eine JSON-Datei in `tests/e2e/cases/` mit einer `description` und den Einstellungen, die von den Vorgaben
abweichen, führen Sie **Gridkeeper tests: update snapshots** dafür aus und schreiben Sie dann die Fallliste neu:

```bash
python3 tests/e2e/write_readme.py
```
