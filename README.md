# Vereinskalender NRW 2027

Das Projekt enthält amtlich belegte Ferientermine und gesetzliche Feiertage für
Nordrhein-Westfalen 2027 sowie ein Python-Skript, das für jede Planungsvariante
in [planungen/](./planungen/) eine Tabellendatei im ODS-Format (LibreOffice/OpenOffice) für die Terminplanung erstellt.
Regeln, Varianten und das JSON-Format sind in
[planungen/erklaerung.md](./planungen/erklaerung.md) beschrieben.

## Voraussetzungen

- Podman
- `podman compose` (nutzt einen installierten Compose-Provider, z. B.
  `docker-compose` oder `podman-compose`)

## ODS-Dateien mit Podman Compose erzeugen

Im Projektverzeichnis ausführen:

```sh
podman compose up --build
```

Für jede JSON-Datei in `planungen/` entsteht eine ODS-Datei mit gleichem
Namen in `output/`, z. B. `planungen/2027-kalenderwoche.json` →
`output/2027-kalenderwoche.ods`. Liegt keine Planungsdatei vor, wird nur
`output/kalender-2027-nrw.ods` mit Ferien und Feiertagen erzeugt.

Beim ersten Aufruf wird das Image gebaut (ca. 520 MB). Dabei werden openpyxl
und LibreOffice Calc installiert: Das Skript baut die Tabelle mit openpyxl und
lässt sie von LibreOffice headless nach ODS umwandeln, damit Farben,
verbundene Zellen und Druckeinstellungen erhalten bleiben. Das Projektverzeichnis ist in den Container eingebunden, deshalb
bleiben die Ausgabedateien nach Ende des Containers erhalten. Änderungen an
Skript oder JSON wirken ohne neuen Build.

Nur bestimmte Planungen erzeugen oder einen anderen Zielordner nutzen:

```sh
podman compose run --rm kalender python generate_calendar.py \
  planungen/2027-kalenderwoche.json --output-dir output/test
```

Weitere Optionen: `--format xlsx` für Excel statt ODS, `--holidays` und
`--vacations` für andere JSON-Dateien (`python generate_calendar.py --help`).

## Tests ausführen

```sh
podman compose run --rm test
```

Die Tests prüfen die JSON-Dateien, die Terminregeln (Wochenzählung, Sperrzeiten,
Cap) und den Inhalt der erzeugten Tabellen.

## Inhalt der ODS-Dateien

- **Jahresübersicht 2027**: alle zwölf Monate nebeneinander im Querformat, auf
  eine A4-Seite skaliert. Je Tag stehen Tageszahl, Wochentag, ggf. Feiertag
  und Vereinstermin sowie montags die Kalenderwoche. Feiertage sind rosa,
  Schulferien gelb, Samstage hellgelb, Sonntage orange und Vereinstermine blau
  markiert.
- **Termine**: alle Termine, die sich aus den Regeln ergeben, mit Status
  „findet statt“ oder „entfällt“ und dem Grund, dazu eine Zusammenfassung.
- **Terminliste 2027**: ein Tag pro Zeile mit Datum, Wochentag, Feiertag,
  Schulferien, Vereinstermin, Uhrzeit, Ort und freier Spalte für Notizen. Mit
  Filter und fixierter Kopfzeile.

`kalender-2027-nrw-querformat.xlsx` (Kalenderpedia) diente nur als optisches
Vorbild und wird vom Skript nicht verwendet.

## Daten und Abgrenzung

- [Schulferien NRW 2027](./schulferien-nrw-2027.json): alle Zeiträume, die das
  Kalenderjahr 2027 berühren. Über den Jahreswechsel reichende Ferien sind
  vollständig angegeben. Quelle: KMK-Ferienkalender 2026/27 und 2027/28,
  Stand 09.10.2025.
- [Gesetzliche Feiertage NRW 2027](./feiertage-nrw-2027.json): die elf
  Feiertage nach § 2 Abs. 1 Feiertagsgesetz NW.
- Bewegliche Ferientage (3 je Schuljahr) fehlen, weil jede Schule sie selbst
  festlegt. Ebenfalls nicht enthalten sind Tage, die kein gesetzlicher Feiertag
  sind, z. B. Rosenmontag, Heiligabend und Silvester.

Alle Datumsangaben in den JSON-Dateien verwenden das ISO-8601-Format
`YYYY-MM-DD`.
