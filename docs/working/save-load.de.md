# Einstellungen speichern und laden { #saving-and-loading-settings }

Jeder Gridkeeper-Dialog hat einen Abschnitt mit Schaltflächen für seine Einstellungen, **Eingaben**.

![Der Abschnitt Eingaben des Behälter-Dialogs mit seinen Schaltflächen für Vorgaben und Einstellungsdateien](../assets/images/dialog-settings-buttons.png)

## Vorgaben des Dialogs { #dialog-defaults }

| Schaltfläche | Was sie bewirkt |
|---|---|
| **Vorgabe setzen** | Der Dialog öffnet sich ab jetzt mit den aktuellen Eingaben |
| **Vorgabe laden** | Setzt die Eingaben auf die gespeicherten Vorgaben zurück |
| **Vorgabe löschen** | Löscht die gespeicherten Vorgaben und setzt die Eingaben auf die ursprünglichen zurück |

Ohne gespeicherte Vorgaben öffnet sich ein Dialog mit den Eingaben, die er zuletzt in dieser Fusion-Sitzung hatte, nach
einem Neustart mit den ursprünglichen. Die Vorgaben werden im Ordner des Add-ins gespeichert und überstehen ein
[Update](../getting-started/installation.md#update).

## Einstellungsdateien { #settings-files }

| Schaltfläche | Was sie bewirkt |
|---|---|
| **In Datei speichern** | Speichert die Einstellungen in einer JSON-Datei |
| **Aus Datei laden** | Setzt die Eingaben aus einer gespeicherten Datei |
| **Kopieren** | Kopiert die Einstellungen als JSON in die Zwischenablage, z. B. für einen Fehlerbericht |

Eine Datei enthält jede Einstellung mit ihrem Namen, Längen in mm und Winkel in Grad, und für welchen Generator sie gilt:

```json
{
    "generator": "label",
    "generatorVersion": "1.0.0",
    "settings": {
        "baseWidth": 42.0,
        "useUnits": true,
        "widthUnits": 1,
        "line1": "M3x10",
        "textStyle": "Heavy",
        "...": "..."
    }
}
```

## Ältere oder andere Dateien laden { #loading-older-or-other-files }

- Eine Datei eines anderen Generators, z. B. eine Grundplatten-Datei im Behälter-Dialog, wird mit einer Meldung
  abgelehnt.
- Ein Wert des falschen Typs lässt die Datei scheitern, und die Meldung nennt die fehlerhafte Einstellung.
- Einstellungen, die die Datei nicht hat, weil eine ältere Version sie gespeichert hat, **behalten den Wert des
  Dialogs**, und eine Meldung listet sie auf; eine Behälter-Datei, die gespeichert wurde, bevor Behälter eine
  Beschriftungsfarbe hatten, behält zum Beispiel die im Dialog gewählte Farbe.
- Einstellungen, die diese Version nicht kennt, werden übersprungen, und eine Auswahl in einer Dropdown-Liste, die sie
  nicht anbietet, wird zu ihrer Vorgabe; die Meldung listet beides auf.

Behälter- und Grundplatten-Dateien, die mit GridfinityGenerator v2.3 oder später gespeichert wurden, werden genauso
geladen.
