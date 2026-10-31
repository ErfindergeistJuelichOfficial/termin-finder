# Hinweise für die Weiterentwicklung

## Projekt

Grundlage für Experimente mit der Terminplanung eines Vereins in NRW.
Ziel ist es, verschiedene Regelvarianten zu vergleichen. Jede Variante ist
eine JSON-Datei in `planungen/`. `generate_calendar.py` erzeugt für jede
Variante eine ODS-Datei `output/<dateiname>.ods`, immer mit Schulferien
und Feiertagen. `planning.py` setzt die Regeln in Termine um. Ausgeführt wird
alles per `podman compose` (siehe README.md).

## Terminplanung

- Regeln, Varianten und JSON-Format stehen in `planungen/erklaerung.md`.
  Bei geänderten Regeln oder neuen Varianten diese Datei mitpflegen,
  einschließlich der Vergleichstabelle (Zahlen aus dem Code ermitteln,
  nicht von Hand zählen).
- Entscheidungen des Nutzers (31.10.2026): Feiertage sind kein
  Hinderungsgrund. „Winterferien“ bedeutet Weihnachtsferien. Bei
  Überschreitung von `max_events_per_week` entfällt der spätere Termin.
  Repair-Café-Wechsel im Quartal: Werkstatt Sa → Stadtbücherei Sa →
  Werkstatt Di.
- Abgesagte Termine nicht stillschweigend verwerfen, sondern mit
  `cancelled_reason` im Blatt „Termine“ zeigen. Der Vergleich der Varianten
  lebt davon.
- Ferienarten für Sperrzeiten werden über das Feld `type` in
  `schulferien-nrw-2027.json` zugeordnet.
- Offen: Ort für „Plenum und Stammtisch“ ist noch nicht festgelegt.

## Regeln

- Projektsprache und Kalenderbeschriftungen sind Deutsch.
- Ferientermine und Feiertage werden ausschließlich aus den JSON-Dateien
  geladen; Termine nicht im Python-Code duplizieren.
- JSON-Daten verwenden ISO-8601-Daten (`YYYY-MM-DD`) und führen die Quellen
  (URL, Stand, Abrufdatum) direkt mit. Ein ISO-Standard für ein
  Ferien-/Feiertags-JSON existiert nicht; das Format ist bewusst einfach
  gehalten.
- Nur geprüfte, amtliche Quellen verwenden:
  - Schulferien: KMK-Ferienkalender (PDF je Schuljahr, z. B.
    `https://www.kmk.org/fileadmin/Dateien/pdf/Ferienkalender/FER2027_28.pdf`).
  - Feiertage: § 2 Abs. 1 Feiertagsgesetz NW auf recht.nrw.de.
  - Findet sich keine Quelle, den Nutzer fragen – er besorgt die Daten.
- Bewegliche Ferientage sind schulspezifisch und dürfen nicht als landesweit
  einheitliche Termine ergänzt werden. Nicht gesetzliche Tage (Rosenmontag,
  Heiligabend, Silvester, Reformationstag, Heilige Drei Könige) gehören nicht
  in `feiertage-nrw-2027.json`.
- Feiertage können ein optionales `short_name` (mit `\n`) für die schmalen
  Zellen der Jahresübersicht haben.

## Ausgabe (ODS)

- Standardformat ist ODS. Die Tabelle wird mit openpyxl als XLSX in einem
  Temp-Ordner gebaut und per `soffice --headless --convert-to ods` umgewandelt
  (LibreOffice ist im Container installiert). `--format xlsx` überspringt die
  Umwandlung. Tests prüfen das XLSX direkt und brauchen kein LibreOffice.

- Blatt „Jahresübersicht 2027“: Querformat, 12 Monatsblöcke nebeneinander
  (je 4 Spalten: Tag, Wochentag, Eintrag, KW), Farben wie in der Vorlage
  (Feiertag rosa, Ferien gelb, Sa hellgelb, So orange), auf eine A4-Seite
  skaliert.
  Vereinstermine erscheinen dort blau mit `short_title`.
- Blatt „Termine“ (nur mit Planung): alle Kandidaten mit Status und Grund
  sowie eine Zusammenfassung.
- Blatt „Terminliste 2027“: ein Tag pro Zeile mit den Spalten
  Vereinstermin, Uhrzeit, Ort und freier Spalte Notizen.
- `kalender-2027-nrw-querformat.xlsx` (© Kalenderpedia) dient nur als
  optisches Vorbild. Die Datei wird weder verändert noch kopiert oder
  eingelesen; das Layout wird vollständig im Skript erzeugt.

## Prüfen nach Änderungen

```sh
podman compose up --build        # ODS-Dateien erzeugen
podman compose run --rm test     # Tests (JSON, Terminregeln, Tabelleninhalt)
```
