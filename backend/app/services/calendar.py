"""
Google Calendar service.
Generates calendar URLs for street sweeping reminders.
"""

import urllib.parse
from datetime import datetime, timedelta
from typing import Union, Dict, Any


def generate_calendar_url(
    sweep: Union[Dict[str, Any], Any],
    address: str,
    reminder_hours: int = 24,
) -> str:
    """
    Generate a Google Calendar URL for the street sweeping event.

    Creates an event for 24 hours BEFORE the sweep (the reminder time).

    Args:
        sweep: The sweep schedule (dict or object with attributes)
        address: The street address
        reminder_hours: Hours before sweep to set reminder (default 24)

    Returns:
        Google Calendar URL
    """
    # Get attributes from dict or object
    if isinstance(sweep, dict):
        corridor = sweep.get("corridor", "")
        blockside = sweep.get("blockside", "")
        limits = sweep.get("limits", "")
        weekday = sweep.get("weekday", "Mon")
        fullname = sweep.get("fullname", "")
        fromhour = sweep.get("fromhour", 9)
        tohour = sweep.get("tohour", 11)
        week1 = sweep.get("week1", True)
        week2 = sweep.get("week2", True)
        week3 = sweep.get("week3", True)
        week4 = sweep.get("week4", True)
        week5 = sweep.get("week5", False)
    else:
        corridor = getattr(sweep, "corridor", "")
        blockside = getattr(sweep, "blockside", "")
        limits = getattr(sweep, "limits", "")
        weekday = getattr(sweep, "weekday", "Mon")
        fullname = getattr(sweep, "fullname", "")
        fromhour = getattr(sweep, "fromhour", 9)
        tohour = getattr(sweep, "tohour", 11)
        week1 = getattr(sweep, "week1", True)
        week2 = getattr(sweep, "week2", True)
        week3 = getattr(sweep, "week3", True)
        week4 = getattr(sweep, "week4", True)
        week5 = getattr(sweep, "week5", False)

    weekday_map = {
        "Mon": 0,
        "Monday": 0,
        "Tues": 1,
        "Tuesday": 1,
        "Wed": 2,
        "Wednesday": 2,
        "Thu": 3,
        "Thursday": 3,
        "Fri": 4,
        "Friday": 4,
        "Sat": 5,
        "Saturday": 5,
        "Sun": 6,
        "Sunday": 6,
    }

    sweep_day = weekday_map.get(weekday, 0)
    today = datetime.now()
    days_until_sweep = (sweep_day - today.weekday()) % 7
    if days_until_sweep == 0:
        days_until_sweep = 7  # Next week if today is the sweep day

    next_sweep = today + timedelta(days=days_until_sweep)
    reminder_time = next_sweep - timedelta(hours=reminder_hours)

    event_start = reminder_time.replace(
        hour=fromhour, minute=0, second=0, microsecond=0
    )
    event_end = event_start + timedelta(hours=1)

    start_str = event_start.strftime("%Y%m%dT%H%M%S")
    end_str = event_end.strftime("%Y%m%dT%H%M%S")

    title = f"Move car: Street sweeping - {corridor}"

    weeks = []
    if week1:
        weeks.append("1st")
    if week2:
        weeks.append("2nd")
    if week3:
        weeks.append("3rd")
    if week4:
        weeks.append("4th")
    if week5:
        weeks.append("5th")
    weeks_str = ", ".join(weeks) if weeks else "weekly"

    details = f"""Street sweeping reminder for {address}

Street: {corridor}
Side: {blockside}
Limits: {limits}
Sweeping: {weekday} {fullname} at {fromhour}:00-{tohour}:00

This event is set for 24 hours before the sweep to give you time to move your car.

Weeks: {weeks_str}
"""

    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": f"{start_str}/{end_str}",
        "details": details,
        "location": address,
    }

    calendar_url = (
        f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"
    )

    return calendar_url


def get_sweep_dates(
    sweep: Union[Dict[str, Any], Any],
    months: int = 3,
) -> list[datetime]:
    """Get the next N occurrences of the sweep day."""
    if isinstance(sweep, dict):
        weekday = sweep.get("weekday", "Mon")
        fromhour = sweep.get("fromhour", 9)
        week1 = sweep.get("week1", True)
        week2 = sweep.get("week2", True)
        week3 = sweep.get("week3", True)
        week4 = sweep.get("week4", True)
        week5 = sweep.get("week5", False)
    else:
        weekday = getattr(sweep, "weekday", "Mon")
        fromhour = getattr(sweep, "fromhour", 9)
        week1 = getattr(sweep, "week1", True)
        week2 = getattr(sweep, "week2", True)
        week3 = getattr(sweep, "week3", True)
        week4 = getattr(sweep, "week4", True)
        week5 = getattr(sweep, "week5", False)

    weekday_map = {
        "Mon": 0,
        "Monday": 0,
        "Tues": 1,
        "Tuesday": 1,
        "Wed": 2,
        "Wednesday": 2,
        "Thu": 3,
        "Thursday": 3,
        "Fri": 4,
        "Friday": 4,
        "Sat": 5,
        "Saturday": 5,
        "Sun": 6,
        "Sunday": 6,
    }

    sweep_day = weekday_map.get(weekday, 0)
    today = datetime.now()

    dates = []
    current = today
    days_until = (sweep_day - current.weekday()) % 7
    if days_until == 0:
        days_until = 7
    current = current + timedelta(days=days_until)

    end_date = today + timedelta(days=months * 30)
    week_flags = [week1, week2, week3, week4, week5]

    while current <= end_date:
        week_of_month = (current.day - 1) // 7

        if week_flags[week_of_month]:
            event_time = current.replace(
                hour=fromhour, minute=0, second=0, microsecond=0
            )
            dates.append(event_time)

        current += timedelta(days=7)

    return dates
