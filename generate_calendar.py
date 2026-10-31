#!/usr/bin/env python3
"""Create 2027 club-planning workbooks from the local JSON data.

One workbook is written per planning file in ``planungen/``. School holidays
and public holidays are always included.
"""

import argparse
import json
import shutil
import subprocess
import tempfile
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from planning import Appointment, Vacation, build_appointments


ROOT = Path(__file__).resolve().parent
WEEKDAYS = (
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
)
MONTHS = (
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
)
LIST_HEADERS = (
    "Datum",
    "Wochentag",
    "Feiertag",
    "Schulferien",
    "Vereinstermin",
    "Uhrzeit",
    "Ort",
    "Notizen",
)
APPOINTMENT_HEADERS = (
    "Datum",
    "Wochentag",
    "KW",
    "Termin",
    "Uhrzeit",
    "Ort",
    "Status",
    "Grund",
)

FONT_NAME = "Arial"
HOLIDAY_COLOR = "FFD9D9"
HOLIDAY_FONT_COLOR = "CC0000"
VACATION_COLOR = "FFFF00"
SATURDAY_COLOR = "FFFFCC"
SUNDAY_COLOR = "FFCC99"
APPOINTMENT_COLOR = "9BC2E6"
CANCELLED_COLOR = "EDEDED"

# Each month in the overview uses four columns: day, weekday, entry, week number.
MONTH_WIDTHS = (3.3, 3.7, 5.7, 2.7)
FIRST_DAY_ROW = 3


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"{path} muss ein JSON-Objekt enthalten.")
    return data


def parse_iso_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Ungültiges ISO-Datum in {field}: {value!r}") from error


def collect_events(
    holiday_data: dict[str, Any],
    vacation_data: dict[str, Any],
) -> tuple[int, dict[date, list[str]], dict[date, list[str]], list[Vacation]]:
    year = holiday_data.get("year")
    if not isinstance(year, int) or vacation_data.get("year") != year:
        raise ValueError("Feiertage und Schulferien müssen dasselbe Jahr angeben.")

    holidays: dict[date, list[str]] = {}
    short_names: dict[date, list[str]] = {}
    for holiday in holiday_data.get("holidays", []):
        day = parse_iso_date(holiday.get("date"), "Feiertag.date")
        if day.year == year:
            holidays.setdefault(day, []).append(holiday["name"])
            short_names.setdefault(day, []).append(
                holiday.get("short_name", holiday["name"])
            )

    vacations: list[Vacation] = []
    for vacation in vacation_data.get("holidays", []):
        start = parse_iso_date(vacation.get("start"), "Schulferien.start")
        end = parse_iso_date(vacation.get("end"), "Schulferien.end")
        if end < start:
            raise ValueError(f"Ferienende liegt vor Ferienbeginn: {vacation!r}")
        if end.year >= year and start.year <= year:
            name = vacation["name"]
            vacations.append(Vacation(start, end, name, vacation.get("type", name)))

    return year, holidays, short_names, vacations


def vacation_names(day: date, vacations: list[Vacation]) -> list[str]:
    return [vacation.name for vacation in vacations if vacation.start <= day <= vacation.end]


def day_fill(day: date, is_holiday: bool, is_vacation: bool) -> PatternFill | None:
    if is_holiday:
        return PatternFill("solid", fgColor=HOLIDAY_COLOR)
    if is_vacation:
        return PatternFill("solid", fgColor=VACATION_COLOR)
    if day.weekday() == 5:
        return PatternFill("solid", fgColor=SATURDAY_COLOR)
    if day.weekday() == 6:
        return PatternFill("solid", fgColor=SUNDAY_COLOR)
    return None


def build_overview_sheet(
    sheet: Worksheet,
    year: int,
    title: str,
    holidays: dict[date, list[str]],
    vacations: list[Vacation],
    appointments: dict[date, list[Appointment]],
) -> None:
    """Landscape year overview: one column block per month, one row per day."""
    last_column = len(MONTHS) * len(MONTH_WIDTHS)
    thin = Side(style="thin", color="808080")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    sheet["A1"] = title
    sheet["A1"].font = Font(name=FONT_NAME, size=24, bold=True)
    sheet["A1"].alignment = Alignment(horizontal="center", vertical="center")
    sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_column)
    sheet.row_dimensions[1].height = 45

    for month in range(1, 13):
        first_column = (month - 1) * len(MONTH_WIDTHS) + 1
        for offset, width in enumerate(MONTH_WIDTHS):
            sheet.column_dimensions[get_column_letter(first_column + offset)].width = width

        header = sheet.cell(2, first_column, MONTHS[month - 1])
        header.font = Font(name=FONT_NAME, size=14, bold=True)
        header.alignment = Alignment(horizontal="center", vertical="center")
        sheet.merge_cells(
            start_row=2,
            start_column=first_column,
            end_row=2,
            end_column=first_column + len(MONTH_WIDTHS) - 1,
        )

        day = date(year, month, 1)
        while day.month == month:
            row = FIRST_DAY_ROW + day.day - 1
            holiday_names = holidays.get(day, [])
            day_appointments = appointments.get(day, [])
            entries = holiday_names + [a.short_title for a in day_appointments]
            is_vacation = bool(vacation_names(day, vacations))
            is_weekend = day.weekday() >= 5
            emphasis = bool(holiday_names) or is_weekend
            font_color = HOLIDAY_FONT_COLOR if holiday_names else None

            cells = [
                sheet.cell(row, first_column, day.day),
                sheet.cell(row, first_column + 1, WEEKDAYS[day.weekday()][:2]),
                sheet.cell(row, first_column + 2, "\n".join(entries) or None),
                sheet.cell(row, first_column + 3),
            ]
            if day.weekday() == 0:
                cells[3].value = day.isocalendar().week
            else:
                sheet.merge_cells(
                    start_row=row,
                    start_column=first_column + 2,
                    end_row=row,
                    end_column=first_column + 3,
                )

            fill = day_fill(day, bool(holiday_names), is_vacation)
            for index, cell in enumerate(cells):
                size = 11 if index < 2 else 7
                bold = (emphasis and index < 2) or (index == 2 and bool(day_appointments))
                cell.font = Font(name=FONT_NAME, size=size, bold=bold, color=font_color)
                cell.border = border
                if index == 2 and day_appointments:
                    cell.fill = PatternFill("solid", fgColor=APPOINTMENT_COLOR)
                elif fill:
                    cell.fill = fill
                horizontal = "center" if index < 2 else "left" if index == 2 else "right"
                vertical = "center" if index < 3 else "bottom"
                cell.alignment = Alignment(
                    horizontal=horizontal, vertical=vertical, wrap_text=index == 2
                )
            day += timedelta(days=1)

    for row in range(FIRST_DAY_ROW, FIRST_DAY_ROW + 31):
        sheet.row_dimensions[row].height = 21

    legend_row = FIRST_DAY_ROW + 31
    legend = [
        ("Feiertag", HOLIDAY_COLOR),
        ("Schulferien", VACATION_COLOR),
        ("Samstag", SATURDAY_COLOR),
        ("Sonntag", SUNDAY_COLOR),
    ]
    if appointments:
        legend.append(("Vereinstermin", APPOINTMENT_COLOR))
    for index, (label, color) in enumerate(legend):
        column = index * 4 + 1
        sheet.cell(legend_row, column).fill = PatternFill("solid", fgColor=color)
        sheet.cell(legend_row, column).border = border
        label_cell = sheet.cell(legend_row, column + 1, label)
        label_cell.font = Font(name=FONT_NAME, size=9)
    note = sheet.cell(
        legend_row,
        last_column,
        "Quellen: KMK-Ferienkalender, Feiertagsgesetz NW · KW = Kalenderwoche",
    )
    note.font = Font(name=FONT_NAME, size=9, italic=True)
    note.alignment = Alignment(horizontal="right")

    sheet.sheet_view.showGridLines = False
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 1
    sheet.print_options.horizontalCentered = True
    sheet.page_margins.left = sheet.page_margins.right = 0.3
    sheet.page_margins.top = sheet.page_margins.bottom = 0.4


def style_table_header(sheet: Worksheet, title: str, headers: tuple[str, ...]) -> None:
    sheet.append([title])
    sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
    sheet["A1"].font = Font(name="Aptos Display", size=16, bold=True, color="FFFFFF")
    sheet["A1"].fill = PatternFill("solid", fgColor="17365D")
    sheet["A1"].alignment = Alignment(vertical="center")
    sheet.row_dimensions[1].height = 30

    sheet.append(list(headers))
    header_fill = PatternFill("solid", fgColor="1F4E78")
    for cell in sheet[2]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    sheet.row_dimensions[2].height = 30


def finish_table(sheet: Worksheet, widths: tuple[int, ...]) -> None:
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    sheet.freeze_panes = "A3"
    sheet.auto_filter.ref = f"A2:{get_column_letter(len(widths))}{sheet.max_row}"
    sheet.sheet_view.showGridLines = False
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.page_setup.orientation = "landscape"
    sheet.print_title_rows = "1:2"


def build_list_sheet(
    sheet: Worksheet,
    year: int,
    holidays: dict[date, list[str]],
    vacations: list[Vacation],
    appointments: dict[date, list[Appointment]],
) -> None:
    """One row per day with columns for club appointments."""
    style_table_header(sheet, f"Vereinskalender Nordrhein-Westfalen {year}", LIST_HEADERS)

    bottom_border = Border(bottom=Side(style="hair", color="D9E1F2"))
    current = date(year, 1, 1)
    final = date(year, 12, 31)
    while current <= final:
        holiday_names = holidays.get(current, [])
        names = vacation_names(current, vacations)
        day_appointments = appointments.get(current, [])
        sheet.append(
            [
                current,
                WEEKDAYS[current.weekday()],
                ", ".join(holiday_names),
                ", ".join(names),
                ", ".join(a.title for a in day_appointments),
                ", ".join(a.time_range for a in day_appointments),
                ", ".join(a.location for a in day_appointments if a.location),
                "",
            ]
        )
        row = sheet.max_row
        sheet.cell(row, 1).number_format = "yyyy-mm-dd"
        fill = day_fill(current, bool(holiday_names), bool(names))
        for cell in sheet[row]:
            cell.border = bottom_border
            if fill:
                cell.fill = fill
            cell.alignment = Alignment(vertical="top", wrap_text=True)
        if day_appointments:
            for column in (5, 6, 7):
                sheet.cell(row, column).fill = PatternFill("solid", fgColor=APPOINTMENT_COLOR)
                sheet.cell(row, column).font = Font(bold=True)
        current += timedelta(days=1)

    finish_table(sheet, (14, 15, 28, 28, 24, 14, 24, 40))


def build_appointment_sheet(
    sheet: Worksheet, plan: dict[str, Any], appointments: list[Appointment]
) -> None:
    """All candidate appointments with status, followed by a short summary."""
    style_table_header(sheet, plan.get("name", "Termine"), APPOINTMENT_HEADERS)

    for appointment in appointments:
        sheet.append(
            [
                appointment.day,
                WEEKDAYS[appointment.day.weekday()],
                appointment.day.isocalendar().week,
                appointment.title,
                appointment.time_range,
                appointment.location,
                "entfällt" if appointment.cancelled_reason else "findet statt",
                appointment.cancelled_reason or "",
            ]
        )
        row = sheet.max_row
        sheet.cell(row, 1).number_format = "yyyy-mm-dd"
        color = CANCELLED_COLOR if appointment.cancelled_reason else APPOINTMENT_COLOR
        for cell in sheet[row]:
            cell.fill = PatternFill("solid", fgColor=color)
            if appointment.cancelled_reason:
                cell.font = Font(color="808080")
    finish_table(sheet, (14, 13, 6, 24, 14, 18, 14, 22))

    summary_column = len(APPOINTMENT_HEADERS) + 2
    held = [a for a in appointments if not a.cancelled_reason]
    summary: list[tuple[str, Any]] = [
        ("Zusammenfassung", None),
        ("Termine gesamt", len(held)),
    ]
    summary += [(f"davon {title}", count) for title, count in Counter(a.title for a in held).items()]
    reasons = Counter(a.cancelled_reason for a in appointments if a.cancelled_reason)
    summary += [(f"entfallen: {reason}", count) for reason, count in reasons.items()]
    for offset, (label, value) in enumerate(summary):
        label_cell = sheet.cell(3 + offset, summary_column, label)
        label_cell.font = Font(bold=offset == 0)
        sheet.cell(3 + offset, summary_column + 1, value)
    sheet.column_dimensions[get_column_letter(summary_column)].width = 30
    sheet.column_dimensions[get_column_letter(summary_column + 1)].width = 8


def build_workbook(
    holiday_data: dict[str, Any],
    vacation_data: dict[str, Any],
    output_path: Path,
    plan: dict[str, Any] | None = None,
) -> None:
    year, holidays, short_names, vacations = collect_events(holiday_data, vacation_data)
    appointments = build_appointments(plan, vacations) if plan else []
    if plan and plan["year"] != year:
        raise ValueError("Planung und Kalenderdaten müssen dasselbe Jahr angeben.")
    held: dict[date, list[Appointment]] = {}
    for appointment in appointments:
        if not appointment.cancelled_reason:
            held.setdefault(appointment.day, []).append(appointment)

    title = f"Vereinskalender {year} Nordrhein-Westfalen"
    if plan:
        title += f" – {plan.get('name', output_path.stem)}"

    workbook = Workbook()
    overview = workbook.active
    overview.title = f"Jahresübersicht {year}"
    build_overview_sheet(overview, year, title, short_names, vacations, held)
    if plan:
        build_appointment_sheet(workbook.create_sheet("Termine"), plan, appointments)
    build_list_sheet(
        workbook.create_sheet(f"Terminliste {year}"), year, holidays, vacations, held
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output_path)


def convert_to_ods(xlsx_paths: list[Path], output_dir: Path) -> list[Path]:
    """Convert workbooks with headless LibreOffice, keeping all formatting."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice is None:
        raise SystemExit(
            "LibreOffice (soffice) nicht gefunden. Skript per podman compose "
            "ausführen oder --format xlsx verwenden."
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as profile_dir:
        subprocess.run(
            [
                soffice,
                f"-env:UserInstallation={Path(profile_dir).as_uri()}",
                "--headless",
                "--convert-to",
                "ods",
                "--outdir",
                str(output_dir),
                *map(str, xlsx_paths),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
    return [output_dir / f"{path.stem}.ods" for path in xlsx_paths]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Erstellt je Planungsdatei einen Vereinskalender (ODS oder XLSX) "
            "mit NRW-Ferien und Feiertagen."
        )
    )
    parser.add_argument(
        "plans",
        nargs="*",
        type=Path,
        help="Planungsdateien (Standard: alle JSON-Dateien in planungen/)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "output",
        help="Zielordner (Standard: output/)",
    )
    parser.add_argument(
        "--holidays",
        type=Path,
        default=ROOT / "feiertage-nrw-2027.json",
        help="JSON-Datei mit gesetzlichen Feiertagen",
    )
    parser.add_argument(
        "--vacations",
        type=Path,
        default=ROOT / "schulferien-nrw-2027.json",
        help="JSON-Datei mit Schulferien",
    )
    parser.add_argument(
        "--format",
        choices=("ods", "xlsx"),
        default="ods",
        help="Ausgabeformat (Standard: ods, benötigt LibreOffice)",
    )
    args = parser.parse_args()

    holiday_data = load_json(args.holidays)
    vacation_data = load_json(args.vacations)
    plan_paths = args.plans or sorted((ROOT / "planungen").glob("*.json"))
    jobs: list[tuple[str, dict[str, Any] | None]] = [
        (plan_path.stem, load_json(plan_path)) for plan_path in plan_paths
    ] or [("kalender-2027-nrw", None)]

    with tempfile.TemporaryDirectory() as temp_dir:
        xlsx_dir = args.output_dir if args.format == "xlsx" else Path(temp_dir)
        xlsx_paths = []
        for name, plan in jobs:
            xlsx_paths.append(xlsx_dir / f"{name}.xlsx")
            build_workbook(holiday_data, vacation_data, xlsx_paths[-1], plan)
        output_paths = (
            convert_to_ods(xlsx_paths, args.output_dir)
            if args.format == "ods"
            else xlsx_paths
        )
    for output_path in output_paths:
        print(f"Kalender erstellt: {output_path}")


if __name__ == "__main__":
    main()
