"""Calendar tool with local ICS fallback and optional CalDAV backend."""

from datetime import datetime, timedelta
from pathlib import Path

import uuid
from caldav import DAVClient
from icalendar import Calendar, Event

from agent.config import settings

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


def _get_caldav_calendar():
    if not (settings.caldav_url and settings.caldav_username and settings.caldav_password):
        return None
    client = DAVClient(
        url=settings.caldav_url,
        username=settings.caldav_username,
        password=settings.caldav_password,
    )
    principal = client.principal()
    calendars = principal.calendars()
    return calendars[0] if calendars else None


async def calendar_list(days_ahead: int = 7) -> str:
    remote_calendar = _get_caldav_calendar()
    if remote_calendar:
        return await _calendar_list_caldav(remote_calendar, days_ahead)
    return await _calendar_list_local(days_ahead)


async def _calendar_list_local(days_ahead: int = 7) -> str:
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
    remote_calendar = _get_caldav_calendar()
    if remote_calendar:
        return await _calendar_add_caldav(remote_calendar, title, start, end, description)
    return await _calendar_add_local(title, start, end, description)


async def _calendar_add_local(title: str, start: str, end: str, description: str = "") -> str:
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


async def _calendar_list_caldav(calendar, days_ahead: int) -> str:
    now = datetime.utcnow()
    cutoff = now + timedelta(days=days_ahead)
    results = calendar.date_search(start=now, end=cutoff)
    events = []
    for result in results:
        component = result.vobject_instance.vevent
        title = str(getattr(component, "summary", None).value if hasattr(component, "summary") else "Untitled")
        start = str(getattr(component, "dtstart", None).value if hasattr(component, "dtstart") else "")
        description = (
            str(getattr(component, "description", None).value)
            if hasattr(component, "description")
            else ""
        )
        events.append({"title": title, "start": start, "description": description})
    if not events:
        return f"No events in the next {days_ahead} days."
    return "\n".join(
        f"• {e['title']} @ {e['start']}" + (f" — {e['description']}" if e["description"] else "")
        for e in sorted(events, key=lambda x: x["start"])
    )


async def _calendar_add_caldav(
    calendar, title: str, start: str, end: str, description: str = ""
) -> str:
    uid = str(uuid.uuid4())
    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//AI Assistant//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}
DTSTART:{datetime.fromisoformat(start).strftime("%Y%m%dT%H%M%S")}
DTEND:{datetime.fromisoformat(end).strftime("%Y%m%dT%H%M%S")}
SUMMARY:{title}
DESCRIPTION:{description}
END:VEVENT
END:VCALENDAR
"""
    calendar.add_event(ics)
    return f"Remote calendar event '{title}' added for {start}."
