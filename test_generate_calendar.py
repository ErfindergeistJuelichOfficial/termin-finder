import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from openpyxl import load_workbook

from generate_calendar import ROOT, build_workbook, collect_events, load_json
from planning import build_appointments, calendar_week_day, nth_weekday


HOLIDAYS = load_json(ROOT / "feiertage-nrw-2027.json")
VACATIONS = load_json(ROOT / "schulferien-nrw-2027.json")
PLAN_FILES = sorted((ROOT / "planungen").glob("*.json"))


class CalendarWorkbookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        output_path = Path(cls.temp_dir.name) / "calendar.xlsx"
        build_workbook(HOLIDAYS, VACATIONS, output_path)
        cls.workbook = load_workbook(output_path, data_only=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()

    def test_overview_sheet_layout(self) -> None:
        sheet = self.workbook["Jahresübersicht 2027"]
        self.assertEqual(sheet.page_setup.orientation, "landscape")
        self.assertEqual(sheet["A2"].value, "Januar")
        self.assertEqual(sheet["AS2"].value, "Dezember")
        # 1 January 2027 is a Friday and a public holiday.
        self.assertEqual(sheet["A3"].value, 1)
        self.assertEqual(sheet["B3"].value, "Fr")
        self.assertEqual(sheet["C3"].value, "Neujahr")
        self.assertEqual(sheet["A3"].fill.fgColor.rgb, "00FFD9D9")
        # 4 January 2027 is a Monday in week 1 during the Christmas holidays.
        self.assertEqual(sheet["D6"].value, 1)
        self.assertEqual(sheet["A6"].fill.fgColor.rgb, "00FFFF00")
        # February has 28 days in 2027.
        self.assertEqual(sheet["E30"].value, 28)
        self.assertIsNone(sheet["E31"].value)
        # Karfreitag, 26 March 2027.
        self.assertEqual(sheet["K28"].value, "Kar-\nfreitag")

    def test_list_sheet_contains_all_days_and_source_events(self) -> None:
        sheet = self.workbook["Terminliste 2027"]
        self.assertEqual(sheet.max_row, 367)
        self.assertEqual(sheet.max_column, 8)
        self.assertEqual(sheet["A3"].value.date(), date(2027, 1, 1))
        self.assertEqual(sheet["C3"].value, "Neujahr")
        self.assertEqual(sheet["D3"].value, "Weihnachtsferien 2026/2027")
        self.assertEqual(sheet["D367"].value, "Weihnachtsferien 2027/2028")
        self.assertIsNone(sheet["E3"].value)

    def test_json_files_are_valid(self) -> None:
        for path in [
            ROOT / "schulferien-nrw-2027.json",
            ROOT / "feiertage-nrw-2027.json",
            *PLAN_FILES,
        ]:
            with path.open(encoding="utf-8") as file:
                self.assertIsInstance(json.load(file), dict)


class PlanningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.vacations = collect_events(HOLIDAYS, VACATIONS)[3]

    def plan(self, week_counting: str) -> dict:
        return load_json(ROOT / "planungen" / f"2027-{week_counting}.json")

    def test_week_counting(self) -> None:
        # September 2027 starts on a Wednesday.
        self.assertEqual(nth_weekday(2027, 9, 1, 1), date(2027, 9, 7))
        self.assertEqual(nth_weekday(2027, 9, 2, 4), date(2027, 9, 10))
        self.assertEqual(calendar_week_day(2027, 9, 1, 1), date(2027, 9, 7))
        self.assertEqual(calendar_week_day(2027, 9, 2, 4), date(2027, 9, 17))
        # Week 4 of April starts on Monday 26 April, its Saturday is in May.
        self.assertEqual(calendar_week_day(2027, 4, 4, 5), date(2027, 5, 1))
        self.assertIsNone(nth_weekday(2027, 2, 5, 0))

    def test_blackouts_and_cap(self) -> None:
        for week_counting in ("kalenderwoche", "n-ter-wochentag"):
            with self.subTest(week_counting=week_counting):
                appointments = build_appointments(self.plan(week_counting), self.vacations)
                held = [a for a in appointments if not a.cancelled_reason]
                self.assertFalse([a for a in held if a.day.month == 9])
                self.assertFalse([a for a in held if date(2027, 7, 19) <= a.day <= date(2027, 8, 31)])
                self.assertFalse([a for a in held if a.day <= date(2027, 1, 6)])
                weeks = [tuple(a.day.isocalendar())[:2] for a in held]
                self.assertEqual(len(weeks), len(set(weeks)))

    def test_cap_cancels_later_appointment(self) -> None:
        appointments = build_appointments(self.plan("n-ter-wochentag"), self.vacations)
        by_day = {a.day: a for a in appointments}
        self.assertIsNone(by_day[date(2027, 4, 6)].cancelled_reason)
        self.assertEqual(by_day[date(2027, 4, 9)].cancelled_reason, "max. 1 pro Woche")

    def test_repair_cafe_rotation(self) -> None:
        appointments = build_appointments(self.plan("kalenderwoche"), self.vacations)
        repair = {a.day.month: a for a in appointments if a.title == "Repair Café" and a.day.year == 2027}
        self.assertEqual(repair[2].location, "Stadtbücherei")
        self.assertEqual(repair[3].day.weekday(), 1)
        self.assertEqual(repair[10].start, "10:00")

    def test_plan_workbooks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            for plan_path in PLAN_FILES:
                output_path = Path(temp_dir) / f"{plan_path.stem}.xlsx"
                build_workbook(HOLIDAYS, VACATIONS, output_path, load_json(plan_path))
                workbook = load_workbook(output_path, data_only=True)
                self.assertEqual(
                    workbook.sheetnames,
                    ["Jahresübersicht 2027", "Termine", "Terminliste 2027"],
                )
                # 2 February 2027 is the first Tuesday in both variants.
                self.assertEqual(workbook["Terminliste 2027"]["E35"].value, "Offene Werkstatt")
                self.assertEqual(workbook["Terminliste 2027"]["F35"].value, "18:00–21:00")


if __name__ == "__main__":
    unittest.main()
