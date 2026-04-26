"""Local calendar tool backed by an ICS file."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from icalendar import Calendar, Event
import uuid

_CAL_FILE = Path("./memory/calendar.ics")


def _load_calendar() -> Calendar:
    if _CAL_FILE.exists():
        return Calendar.from_ical(_CAL_FILE.read_bytes())
    cal = Calendar()
    cal.add("prodid", "-//AI Assistant//EN")
    cal.add("version", "2.0")
    return cal


def _save_calendar(cal: Calendar):
    _CAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CAL_FILE.write_bytes(cal.to_ical())


async def calendar_list(days_ahead: int = 7) -> str:
    cal = _load_calendar()
    now = datetime.utcnow()
    cutoff = now + timedelta(days=days_ahead)
    events = []
    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        start = component.get("dtstart")
        if start is None:
            continue
        start_dt = start.dt
        if hasattr(start_dt, "date"):
            start_dt = datetime.combine(start_dt, datetime.min.time())
        if now <= start_dt <= cutoff:
            events.append(
                {
                    "title": str(component.get("summary", "Untitled")),
                    "start": str(start.dt),
                    "description": str(component.get("description", "")),
                }
            )
    if not events:
        return f"No events in the next {days_ahead} days."
    return "\n".join(
        f"• {e['title']} @ {e['start']}" + (f" — {e['description']}" if e["description"] else "")
        for e in sorted(events, key=lambda x: x["start"])
    )


async def calendar_add(title: str, start: str, end: str, description: str = "") -> str:
    cal = _load_calendar()
    event = Event()
    event.add("summary", title)
    event.add("dtstart", datetime.fromisoformat(start))
    event.add("dtend", datetime.fromisoformat(end))
    event.add("description", description)
    event["uid"] = str(uuid.uuid4())
    cal.add_component(event)
    _save_calendar(cal)
    return f"Event '{title}' added for {start}."
