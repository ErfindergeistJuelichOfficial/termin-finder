"""Derive club appointments from a planning JSON file."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, NamedTuple


WEEKDAY_INDEX = {
    "Montag": 0,
    "Dienstag": 1,
    "Mittwoch": 2,
    "Donnerstag": 3,
    "Freitag": 4,
    "Samstag": 5,
    "Sonntag": 6,
}
WEEK_COUNTING = ("kalenderwoche", "n-ter-wochentag")


class Vacation(NamedTuple):
    start: date
    end: date
    name: str
    kind: str


@dataclass
class Appointment:
    day: date
    title: str
    short_title: str
    start: str
    end: str
    location: str
    cancelled_reason: str | None = None

    @property
    def time_range(self) -> str:
        return f"{self.start}–{self.end}"


def nth_weekday(year: int, month: int, week: int, weekday: int) -> date | None:
    """The n-th occurrence of a weekday in a month, e.g. the 2nd Friday."""
    first = date(year, month, 1)
    day = first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (week - 1))
    return day if day.month == month else None


def calendar_week_day(year: int, month: int, week: int, weekday: int) -> date | None:
    """Weekday in the n-th calendar week whose Monday lies in the month.

    The resulting day may fall into the following month (e.g. a Saturday
    after the last Monday of a month).
    """
    monday = nth_weekday(year, month, week, 0)
    return monday + timedelta(days=weekday) if monday else None


def validate_plan(plan: dict[str, Any]) -> None:
    if plan.get("week_counting") not in WEEK_COUNTING:
        raise ValueError(f"week_counting muss einer von {WEEK_COUNTING} sein.")
    if not isinstance(plan.get("year"), int):
        raise ValueError("Planung braucht ein ganzzahliges year.")
    for rule in plan.get("rules", []):
        if rule.get("weekday") not in WEEKDAY_INDEX:
            raise ValueError(f"Unbekannter Wochentag in Regel: {rule!r}")
        if rule.get("week") not in (1, 2, 3, 4, 5):
            raise ValueError(f"week muss zwischen 1 und 5 liegen: {rule!r}")


def blackout_reason(
    day: date, blackout: dict[str, Any], vacations: list[Vacation]
) -> str | None:
    if day.month in blackout.get("months", []):
        return "Monat gesperrt"
    for vacation in vacations:
        if vacation.kind in blackout.get("school_holidays", []):
            if vacation.start <= day <= vacation.end:
                return vacation.kind
    return None


def build_appointments(
    plan: dict[str, Any], vacations: list[Vacation]
) -> list[Appointment]:
    """All candidate appointments of the year, cancelled ones with a reason."""
    validate_plan(plan)
    year = plan["year"]
    find_day = (
        calendar_week_day if plan["week_counting"] == "kalenderwoche" else nth_weekday
    )

    appointments: list[Appointment] = []
    for month in range(1, 13):
        for rule in plan.get("rules", []):
            if month not in rule.get("months", range(1, 13)):
                continue
            day = find_day(year, month, rule["week"], WEEKDAY_INDEX[rule["weekday"]])
            if day is None:
                continue
            appointments.append(
                Appointment(
                    day=day,
                    title=rule["title"],
                    short_title=rule.get("short_title", rule["title"]),
                    start=rule["start"],
                    end=rule["end"],
                    location=rule.get("location", ""),
                )
            )
    appointments.sort(key=lambda appointment: appointment.day)

    blackout = plan.get("blackout", {})
    for appointment in appointments:
        appointment.cancelled_reason = blackout_reason(
            appointment.day, blackout, vacations
        )

    # Earlier appointments win when a calendar week exceeds the cap.
    cap = plan.get("max_events_per_week")
    if cap is not None:
        per_week: dict[tuple[int, int], int] = {}
        for appointment in appointments:
            if appointment.cancelled_reason:
                continue
            week = tuple(appointment.day.isocalendar())[:2]
            if per_week.get(week, 0) >= cap:
                appointment.cancelled_reason = f"max. {cap} pro Woche"
            else:
                per_week[week] = per_week.get(week, 0) + 1

    return appointments
