# Terminplanung 2027: Regeln und Varianten

In diesem Ordner liegt eine JSON-Datei pro Planungsvariante. Für jede Datei
erzeugt `generate_calendar.py` eine eigene Tabellendatei (ODS) in `output/` mit
demselben Namen, z. B. `2027-kalenderwoche.json` →
`output/2027-kalenderwoche.ods`. Schulferien und gesetzliche Feiertage sind
in jeder Datei enthalten.

## Aktuelle Regeln (Stand 31.10.2026)

| Woche im Monat | Tag | Uhrzeit | Termin | Ort |
| --- | --- | --- | --- | --- |
| 1. Woche | Dienstag | 18–21 Uhr | Offene Werkstatt | Werkstatt |
| 2. Woche | Freitag | 19–22 Uhr | Plenum und Stammtisch | – (noch offen) |
| 3. Woche | Samstag | 16–20 Uhr | Offene Werkstatt | Werkstatt |
| 4. Woche | wechselnd | siehe unten | Repair Café | wechselnd |

Repair Café, Wechsel innerhalb jedes Quartals:

| Monat im Quartal | Monate | Tag | Uhrzeit | Ort |
| --- | --- | --- | --- | --- |
| 1. | Jan, Apr, Jul, Okt | Samstag | 10–14 Uhr | Werkstatt |
| 2. | Feb, Mai, Aug, Nov | Samstag | 10–12:30 Uhr | Stadtbücherei |
| 3. | Mär, Jun, Sep, Dez | Dienstag | 18–21 Uhr | Werkstatt |

Außerdem gilt:

- **Höchstens 1 Veranstaltung pro Kalenderwoche** (Montag bis Sonntag).
- **Keine Termine** im September, in den Sommerferien (19.07.–31.08.2027) und
  in den Weihnachtsferien (bis 06.01.2027 und ab 24.12.2027). NRW hat keine
  Winterferien. Gemeint sind deshalb die Weihnachtsferien.
- **Oster-, Pfingst- und Herbstferien** sind keine Sperrzeiten.
- **Gesetzliche Feiertage** sind kein Hinderungsgrund. Der Termin findet
  trotzdem statt.

## Die zwei Varianten: Was ist „Woche im Monat“?

### `2027-kalenderwoche.json`

Woche *n* ist die *n*-te Kalenderwoche, deren **Montag im Monat liegt**. Der
Termin ist der jeweilige Wochentag dieser Woche.

- Termine können nie in derselben Woche liegen. Die Regel „1 pro Woche“ greift
  daher nie.
- Ein Samstag kann in den Folgemonat rutschen. Beispiel: Die 4. Woche im April
  beginnt am Mo 26.04., das Repair Café ist dann am **Sa 01.05.** (Feiertag).
  Im Mai gibt es dadurch zwei Repair Cafés (01.05. und 29.05.), im April keins.
- Die Termine liegen tendenziell später im Monat. Beispiel: Plenum am Fr 15.01.
  statt Fr 08.01.

### `2027-n-ter-wochentag.json`

Woche *n* ist das *n*-te Vorkommen des Wochentags im Monat: 1. Dienstag,
2. Freitag, 3. Samstag, 4. Samstag bzw. Dienstag. So zählen viele Vereine.

- Alle Termine bleiben im richtigen Monat.
- Der 1. Dienstag und der 2. Freitag können in dieselbe Kalenderwoche fallen.
  Dann gilt die Cap-Regel, und der **spätere Termin entfällt**. 2027 betrifft
  das viermal das Plenum (09.04., 09.07., 08.10., 10.12.) und einmal die
  Samstags-Werkstatt (15.05.).

### Vergleich 2027

| | Kalenderwoche | n-ter Wochentag |
| --- | --- | --- |
| Termine gesamt | **35** | **32** |
| Offene Werkstatt | 17 | 18 |
| Plenum und Stammtisch | 10 | 6 |
| Repair Café | 8 | 8 |
| entfallen wegen Sommerferien | 6 | 5 |
| entfallen wegen September | 4 | 4 |
| entfallen wegen Weihnachtsferien | 3 | 2 |
| entfallen wegen „max. 1 pro Woche“ | 0 | 5 |
| Monate ohne Termin | Aug, Sep | Aug, Sep |

Im Juli gibt es nur Termine vor Beginn der Sommerferien am 19.07. Die genauen
Termine stehen jeweils im Blatt „Termine“ der ODS-Datei.

## Aufbau der ODS-Datei

- **Jahresübersicht 2027**: alle Monate nebeneinander im Querformat, mit
  Feiertagen, Schulferien und den stattfindenden Vereinsterminen (blau).
- **Termine**: alle Termine, die sich aus den Regeln ergeben, mit Status
  „findet statt“ oder „entfällt“ und dem Grund. Rechts daneben eine
  Zusammenfassung.
- **Terminliste 2027**: ein Tag pro Zeile, Vereinstermin, Uhrzeit und Ort sind
  ausgefüllt, die Spalte „Notizen“ ist frei.

## Aufbau einer Planungsdatei

```json
{
  "name": "Anzeigename (erscheint im Titel der Tabelle)",
  "description": "Kurze Beschreibung der Variante",
  "year": 2027,
  "week_counting": "kalenderwoche",
  "max_events_per_week": 1,
  "blackout": {
    "months": [9],
    "school_holidays": ["Sommerferien", "Weihnachtsferien"]
  },
  "rules": [
    {
      "title": "Offene Werkstatt",
      "short_title": "Offene\nWerkstatt",
      "week": 1,
      "weekday": "Dienstag",
      "start": "18:00",
      "end": "21:00",
      "location": "Werkstatt",
      "months": [1, 4, 7, 10]
    }
  ]
}
```

| Feld | Bedeutung |
| --- | --- |
| `week_counting` | `kalenderwoche` oder `n-ter-wochentag` (siehe oben) |
| `max_events_per_week` | Obergrenze je Kalenderwoche. Weitere Termine entfallen, der frühere bleibt. Weglassen = keine Grenze. |
| `blackout.months` | Monate (1–12) ohne Termine |
| `blackout.school_holidays` | Ferienarten ohne Termine. Möglich sind: `Weihnachtsferien`, `Osterferien`, `Pfingstferien`, `Sommerferien`, `Herbstferien` |
| `rules[].week` | Woche im Monat (1–5). Gibt es die Woche im Monat nicht, entfällt der Termin. |
| `rules[].weekday` | Wochentag auf Deutsch (`Montag` … `Sonntag`) |
| `rules[].start` / `end` | Uhrzeit als Text (`HH:MM`) |
| `rules[].location` | Ort (optional) |
| `rules[].months` | nur in diesen Monaten (optional, sonst jeden Monat) |
| `rules[].short_title` | Kurzform für die schmalen Zellen der Jahresübersicht, `\n` = Zeilenumbruch (optional) |

Für eine neue Variante eine bestehende Datei kopieren, umbenennen und
anpassen. Danach `podman compose up` ausführen.
