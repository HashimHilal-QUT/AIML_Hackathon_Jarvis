"""
JARVIS Calendar Parser
======================
Converts calendar file formats (.ics, .csv, .xml) into LLM-friendly JSON.
Also supports fetching live Outlook calendars via ICS subscription URL
(works with Microsoft 365 / university Outlook accounts).

Supported formats:
  - .ics  : iCalendar (Google Calendar, Apple Calendar, Outlook)
  - .csv  : Google Calendar CSV export
  - .xml  : Outlook XML export
  - URL   : Live Outlook ICS subscription URL (Option 1 — no export needed)

Install dependencies:
  pip install fastapi uvicorn icalendar python-multipart requests
"""

import json
import csv
import xml.etree.ElementTree as ET
from io import StringIO
from datetime import datetime, date
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from urllib.parse import urlparse

import requests as http_requests
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from icalendar import Calendar

app = FastAPI(
    title="JARVIS Calendar Parser",
    description="Converts calendar files into LLM-friendly JSON for the scheduling reminder agent.",
    version="1.0.0"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def serialize_dt(value: Any) -> str | None:
    """Safely convert datetime / date / vDatetime to ISO string."""
    if value is None:
        return None
    if hasattr(value, "dt"):          # icalendar vDDDLists / vDatetime wrapper
        value = value.dt
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day).isoformat()
    return str(value)


def normalize_timezone(tz_str: str | None) -> str | None:
    """Return IANA timezone string if valid, else None."""
    if not tz_str:
        return None
    try:
        ZoneInfo(str(tz_str))
        return str(tz_str)
    except (ZoneInfoNotFoundError, KeyError):
        return str(tz_str)   # keep raw value so LLM can still reason about it


def build_llm_envelope(events: list[dict], source_format: str, filename: str) -> dict:
    """Wrap events in a structured envelope the LLM can parse reliably."""
    return {
        "jarvis_calendar_data": {
            "metadata": {
                "source_format": source_format,
                "filename": filename,
                "parsed_at": datetime.utcnow().isoformat() + "Z",
                "total_events": len(events)
            },
            "events": events
        }
    }


# ---------------------------------------------------------------------------
# ICS Parser
# ---------------------------------------------------------------------------

def parse_ics(content: bytes, filename: str) -> dict:
    cal = Calendar.from_ical(content)
    events = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        # Recurrence rule
        rrule = None
        if component.get("RRULE"):
            rrule_dict = dict(component.get("RRULE"))
            # Convert lists to plain values where possible
            rrule = {k: (v[0] if isinstance(v, list) and len(v) == 1 else v)
                     for k, v in rrule_dict.items()}

        # Attendees — can be a list or single value
        raw_attendees = component.get("ATTENDEE", [])
        if not isinstance(raw_attendees, list):
            raw_attendees = [raw_attendees]
        attendees = [str(a) for a in raw_attendees]

        event = {
            "id":           str(component.get("UID", "")),
            "title":        str(component.get("SUMMARY", "Untitled")),
            "description":  str(component.get("DESCRIPTION", "")),
            "location":     str(component.get("LOCATION", "")),
            "start":        serialize_dt(component.get("DTSTART")),
            "end":          serialize_dt(component.get("DTEND")),
            "all_day":      isinstance(
                                getattr(component.get("DTSTART"), "dt", None), date
                            ) and not isinstance(
                                getattr(component.get("DTSTART"), "dt", None), datetime
                            ),
            "timezone":     normalize_timezone(
                                str(component.get("DTSTART").params.get("TZID", ""))
                                if component.get("DTSTART") else None
                            ),
            "status":       str(component.get("STATUS", "CONFIRMED")),
            "organizer":    str(component.get("ORGANIZER", "")),
            "attendees":    attendees,
            "recurrence":   rrule,
            "created":      serialize_dt(component.get("CREATED")),
            "last_modified": serialize_dt(component.get("LAST-MODIFIED")),
            "url":          str(component.get("URL", "")),
        }
        events.append(event)

    return build_llm_envelope(events, "ics", filename)


# ---------------------------------------------------------------------------
# CSV Parser  (Google Calendar export format)
# ---------------------------------------------------------------------------

# Google Calendar CSV column mapping → our normalised keys
GOOGLE_CSV_MAP = {
    "Subject":      "title",
    "Start Date":   "start_date",
    "Start Time":   "start_time",
    "End Date":     "end_date",
    "End Time":     "end_time",
    "All Day Event": "all_day",
    "Description":  "description",
    "Location":     "location",
    "Private":      "private",
}


def parse_google_csv_datetime(date_str: str, time_str: str) -> str | None:
    """Combine Google CSV date + time strings into ISO datetime."""
    date_str = date_str.strip()
    time_str = time_str.strip() if time_str else ""
    if not date_str:
        return None
    fmt_date = "%m/%d/%Y"
    try:
        if time_str:
            dt = datetime.strptime(f"{date_str} {time_str}", f"{fmt_date} %I:%M %p")
        else:
            dt = datetime.strptime(date_str, fmt_date)
        return dt.isoformat()
    except ValueError:
        return f"{date_str} {time_str}".strip()


def parse_csv(content: bytes, filename: str) -> dict:
    text = content.decode("utf-8-sig")   # handle BOM from Windows exports
    reader = csv.DictReader(StringIO(text))
    events = []

    for i, row in enumerate(reader):
        # Detect Google Calendar format vs generic CSV
        if "Subject" in row:
            event = {
                "id":          str(i),
                "title":       row.get("Subject", "Untitled"),
                "description": row.get("Description", ""),
                "location":    row.get("Location", ""),
                "start":       parse_google_csv_datetime(
                                   row.get("Start Date", ""),
                                   row.get("Start Time", "")
                               ),
                "end":         parse_google_csv_datetime(
                                   row.get("End Date", ""),
                                   row.get("End Time", "")
                               ),
                "all_day":     row.get("All Day Event", "False").strip().lower() == "true",
                "timezone":    None,
                "status":      "CONFIRMED",
                "organizer":   "",
                "attendees":   [],
                "recurrence":  None,
                "private":     row.get("Private", "False").strip().lower() == "true",
            }
        else:
            # Generic CSV — map columns as-is
            event = {"id": str(i), **{k: v for k, v in row.items()}}

        events.append(event)

    return build_llm_envelope(events, "csv", filename)


# ---------------------------------------------------------------------------
# XML Parser  (Outlook XML export format)
# ---------------------------------------------------------------------------

# Outlook XML uses a namespace
OUTLOOK_NS = {
    "o": "http://schemas.microsoft.com/mapi/2007"
}


def xml_text(element, tag: str, ns: dict | None = None) -> str:
    """Safely extract text from an XML child element."""
    if ns:
        child = element.find(f"o:{tag}", ns)
    else:
        child = element.find(tag)
    return child.text.strip() if child is not None and child.text else ""


def parse_xml(content: bytes, filename: str) -> dict:
    root = ET.fromstring(content)
    events = []

    # Support both Outlook-namespaced XML and generic calendar XML
    # Try namespaced first
    items = root.findall(".//o:item", OUTLOOK_NS) or root.findall(".//item")

    for i, item in enumerate(items):
        ns = OUTLOOK_NS if root.findall(".//o:item", OUTLOOK_NS) else None

        start_raw = xml_text(item, "dtStart", ns) or xml_text(item, "start", ns)
        end_raw   = xml_text(item, "dtEnd",   ns) or xml_text(item, "end",   ns)

        # Try to parse Outlook's datetime format
        def outlook_dt(raw: str) -> str | None:
            if not raw:
                return None
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(raw, fmt).isoformat()
                except ValueError:
                    continue
            return raw

        event = {
            "id":           xml_text(item, "uid",         ns) or str(i),
            "title":        xml_text(item, "subject",     ns) or xml_text(item, "title", ns) or "Untitled",
            "description":  xml_text(item, "body",        ns) or xml_text(item, "description", ns),
            "location":     xml_text(item, "location",    ns),
            "start":        outlook_dt(start_raw),
            "end":          outlook_dt(end_raw),
            "all_day":      xml_text(item, "allDayEvent", ns).lower() in ("true", "1", "yes"),
            "timezone":     xml_text(item, "timeZone",    ns) or None,
            "status":       xml_text(item, "status",      ns) or "CONFIRMED",
            "organizer":    xml_text(item, "organizer",   ns),
            "attendees":    [a.text.strip() for a in
                             (item.findall("o:attendee", ns) if ns else item.findall("attendee"))
                             if a.text],
            "recurrence":   xml_text(item, "recurrence",  ns) or None,
        }
        events.append(event)

    return build_llm_envelope(events, "xml", filename)


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

def parse_calendar(content: bytes, filename: str) -> dict:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "ics":
        return parse_ics(content, filename)
    elif ext == "csv":
        return parse_csv(content, filename)
    elif ext == "xml":
        return parse_xml(content, filename)
    else:
        raise ValueError(f"Unsupported file format: .{ext} — supported: .ics, .csv, .xml")


# ---------------------------------------------------------------------------
# FastAPI Endpoints
# ---------------------------------------------------------------------------

@app.post("/calendar/parse", summary="Upload a calendar file and get LLM-ready JSON")
async def upload_calendar(file: UploadFile = File(...)):
    """
    Upload a .ics, .csv, or .xml calendar file.
    Returns structured JSON ready to be passed to the JARVIS scheduling agent.
    """
    allowed_extensions = {"ics", "csv", "xml"}
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Allowed: .ics, .csv, .xml"
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        result = parse_calendar(content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse calendar file: {str(e)}")

    return JSONResponse(content=result)


@app.get("/calendar/health", summary="Health check")
def health():
    return {"status": "ok", "service": "JARVIS Calendar Parser"}


# ---------------------------------------------------------------------------
# Outlook ICS URL Subscription (Option 1 — Live feed, no export needed)
# ---------------------------------------------------------------------------

ALLOWED_ICS_HOSTS = {
    "outlook.live.com",
    "outlook.office.com",
    "outlook.office365.com",
    "calendar.google.com",        # Google Calendar ICS URLs
    "mytimetable.qut.edu.au",     # QUT student class timetable
    "canvas.qut.edu.au",          # QUT Canvas assignment & event reminders
}

def validate_ics_url(url: str) -> str:
    """Validate the URL is from a trusted calendar host and uses HTTPS."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise HTTPException(
            status_code=400,
            detail="Only HTTPS ICS URLs are allowed for security."
        )
    if parsed.netloc not in ALLOWED_ICS_HOSTS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Untrusted host '{parsed.netloc}'. "
                f"Allowed hosts: {', '.join(sorted(ALLOWED_ICS_HOSTS))}"
            )
        )
    return url


def fetch_ics_from_url(ics_url: str) -> bytes:
    """Fetch raw ICS content from a live Outlook/Google Calendar subscription URL."""
    try:
        response = http_requests.get(
            ics_url,
            timeout=15,
            headers={
                "User-Agent": "JARVIS-Calendar-Agent/1.0",
                "Accept": "text/calendar, application/ics, */*",
            }
        )
        response.raise_for_status()
        return response.content
    except http_requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request to calendar URL timed out.")
    except http_requests.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail="Could not connect to the calendar URL.")
    except http_requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Calendar URL returned error: {str(e)}")


@app.get(
    "/calendar/outlook",
    summary="Fetch live calendar via ICS subscription URL",
    description=(
        "Pass any supported ICS subscription URL as a query parameter. "
        "JARVIS fetches it live and returns LLM-ready JSON — no file export needed.\n\n"
        "**Supported Sources:**\n"
        "- **Outlook** (Microsoft 365 / university email calendar)\n"
        "- **QUT Timetable** (`mytimetable.qut.edu.au`) — class schedule\n"
        "- **QUT Canvas** (`canvas.qut.edu.au`) — assignment due dates & events\n"
        "- **Google Calendar** (`calendar.google.com`)\n\n"
        "**How to get your QUT Timetable ICS URL:**\n"
        "1. Go to mytimetable.qut.edu.au\n"
        "2. Click the calendar subscription/export button\n"
        "3. Copy the ICS link\n\n"
        "**How to get your QUT Canvas ICS URL:**\n"
        "1. Go to canvas.qut.edu.au → Calendar\n"
        "2. Click 'Calendar Feed' at the bottom right\n"
        "3. Copy the ICS link"
    )
)
async def fetch_outlook_calendar(
    ics_url: str = Query(
        ...,
        description="Your Outlook ICS subscription URL (must be HTTPS from outlook.live.com or outlook.office365.com)",
        example="https://outlook.live.com/owa/calendar/00000000.../reachable/en-AU.ics"
    )
):
    validate_ics_url(ics_url)
    content = fetch_ics_from_url(ics_url)

    # Extract a clean filename from the URL for the metadata envelope
    filename = ics_url.split("/")[-1].split("?")[0] or "outlook_calendar.ics"
    if not filename.endswith(".ics"):
        filename = "outlook_calendar.ics"

    try:
        result = parse_ics(content, filename)
        # Tag source as outlook in metadata
        result["jarvis_calendar_data"]["metadata"]["source"] = "outlook_ics_url"
        result["jarvis_calendar_data"]["metadata"]["ics_url"] = ics_url
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse Outlook calendar: {str(e)}")

    return JSONResponse(content=result)


# ---------------------------------------------------------------------------
# LLM Prompt Helper  (utility — not an endpoint)
# ---------------------------------------------------------------------------

def build_llm_prompt(calendar_json: dict) -> str:
    """
    Wraps the parsed calendar JSON into a prompt string
    ready to be passed to the OpenAI / Claude API.
    """
    data = calendar_json.get("jarvis_calendar_data", {})
    events = data.get("events", [])
    meta = data.get("metadata", {})

    prompt = f"""You are JARVIS, an intelligent scheduling assistant.
Below is the user's calendar data parsed from a {meta.get('source_format', 'calendar').upper()} file.
It contains {meta.get('total_events', 0)} events. Analyse the schedule and help the user with reminders,
conflicts, and suggestions.

CALENDAR DATA:
{json.dumps(events, indent=2)}

Today's date and time (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}

Based on this calendar:
1. List any upcoming events in the next 7 days.
2. Identify any scheduling conflicts.
3. Suggest reminders for important events.
"""
    return prompt


# ---------------------------------------------------------------------------
# Run locally
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("calendar_parser:app", host="0.0.0.0", port=8001, reload=True)
