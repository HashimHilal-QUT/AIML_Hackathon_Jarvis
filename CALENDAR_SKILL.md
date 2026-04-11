# 🗓️ JARVIS Calendar Skill

## Skill Overview
This skill allows JARVIS to fetch, parse, and reason about student calendar data from multiple sources including QUT class timetables, Canvas assignment deadlines, Outlook, and Google Calendar. All sources are normalised into the same JSON structure so JARVIS can cross-reference events, detect conflicts, and deliver smart reminders.

---

## Supported Calendar Sources

| Source | Domain | What it contains |
|---|---|---|
| QUT Timetable | `mytimetable.qut.edu.au` | Class schedule, lecture times, room locations |
| QUT Canvas | `canvas.qut.edu.au` | Assignment due dates, quiz deadlines, course events |
| Microsoft Outlook | `outlook.live.com`, `outlook.office.com`, `outlook.office365.com` | Personal calendar, university email events |
| Google Calendar | `calendar.google.com` | Personal events |
| File Upload | `.ics`, `.csv`, `.xml` | Any exported calendar file |

---

## API Endpoints

### 1. Fetch Live Calendar via ICS URL
```
GET /calendar/outlook?ics_url=<URL>
```
Use this for all live subscription feeds (QUT Timetable, Canvas, Outlook, Google).

**Examples:**
```bash
# QUT Class Timetable
GET /calendar/outlook?ics_url=https://mytimetable.qut.edu.au/aplus/rest/calendar/ical/<uuid>

# QUT Canvas Assignments
GET /calendar/outlook?ics_url=https://canvas.qut.edu.au/feeds/calendars/user_<token>.ics

# Outlook Calendar
GET /calendar/outlook?ics_url=https://outlook.live.com/owa/calendar/<id>/reachable/en-AU.ics
```

---

### 2. Upload a Calendar File
```
POST /calendar/parse
Content-Type: multipart/form-data
Body: file=<file.ics | file.csv | file.xml>
```
Use this when the student has exported a calendar file manually.

---

### 3. Health Check
```
GET /calendar/health
```
Returns `{"status": "ok"}` if the service is running.

---

## Normalised Event JSON Structure

Every calendar source returns events in this unified format:

```json
{
  "jarvis_calendar_data": {
    "metadata": {
      "source_format": "ics",
      "filename": "qut_timetable.ics",
      "source": "outlook_ics_url",
      "ics_url": "https://mytimetable.qut.edu.au/...",
      "parsed_at": "2026-04-11T10:00:00Z",
      "total_events": 12
    },
    "events": [
      {
        "id": "unique-event-id",
        "title": "CAB301 Lecture",
        "description": "Algorithms and Complexity",
        "location": "P Block, Level 4, Room P401",
        "start": "2026-04-14T10:00:00",
        "end": "2026-04-14T12:00:00",
        "all_day": false,
        "timezone": "Australia/Brisbane",
        "status": "CONFIRMED",
        "organizer": "lecturer@qut.edu.au",
        "attendees": [],
        "recurrence": { "FREQ": "WEEKLY", "BYDAY": "MO" },
        "created": "2026-01-01T00:00:00",
        "last_modified": "2026-03-01T00:00:00",
        "url": ""
      }
    ]
  }
}
```

---

## How JARVIS Should Use This Skill

### Step 1 — Fetch the student's calendars
Always fetch BOTH QUT sources to get the full picture:

```python
import requests

BASE_URL = "http://localhost:8001"

def get_student_calendar(timetable_ics_url: str, canvas_ics_url: str) -> list[dict]:
    """Fetch and merge QUT timetable + Canvas events."""
    
    timetable = requests.get(
        f"{BASE_URL}/calendar/outlook",
        params={"ics_url": timetable_ics_url}
    ).json()

    canvas = requests.get(
        f"{BASE_URL}/calendar/outlook",
        params={"ics_url": canvas_ics_url}
    ).json()

    timetable_events = timetable["jarvis_calendar_data"]["events"]
    canvas_events    = canvas["jarvis_calendar_data"]["events"]

    # Tag each event with its source so JARVIS can differentiate
    for e in timetable_events:
        e["source"] = "qut_timetable"
    for e in canvas_events:
        e["source"] = "canvas_assignment"

    return timetable_events + canvas_events
```

---

### Step 2 — Build the LLM prompt
Pass the merged events into the LLM with this prompt template:

```python
import json
from datetime import datetime

def build_jarvis_calendar_prompt(events: list[dict], user_query: str) -> str:
    today = datetime.now().strftime("%A, %d %B %Y %H:%M")
    
    # Separate event types for clarity
    classes     = [e for e in events if e.get("source") == "qut_timetable"]
    assignments = [e for e in events if e.get("source") == "canvas_assignment"]
    other       = [e for e in events if e.get("source") not in ("qut_timetable", "canvas_assignment")]

    return f"""You are JARVIS, an intelligent scheduling assistant for a QUT university student.
Today is {today} (Brisbane time, AEST).

You have access to the student's full schedule broken into three categories:

## CLASSES & LECTURES ({len(classes)} events)
{json.dumps(classes, indent=2)}

## ASSIGNMENT DUE DATES ({len(assignments)} events)
{json.dumps(assignments, indent=2)}

## OTHER EVENTS ({len(other)} events)
{json.dumps(other, indent=2)}

## STUDENT'S REQUEST
{user_query}

## YOUR TASK
Respond as JARVIS. Be concise, helpful, and proactive. When relevant:
- Flag upcoming deadlines in the next 7 days
- Warn about clashes between classes and assignment due dates
- Suggest when the student should start working on assignments
- Remind the student of tomorrow's classes at end of day
- Use 24hr time and Brisbane timezone (AEST/AEDT) in all responses
"""
```

---

### Step 3 — Example JARVIS responses

**User:** "What do I have on tomorrow?"
```
JARVIS response should list:
- All classes with times and room locations
- Any assignments due tomorrow or the day after
- Any other calendar events
```

**User:** "Am I free this afternoon?"
```
JARVIS response should:
- Check today's events between now and end of day
- Confirm free slots or flag any clashes
```

**User:** "When should I work on my assignment?"
```
JARVIS response should:
- Find the assignment due date from Canvas events
- Cross-check against class timetable
- Suggest free blocks of time before the deadline
```

---

## Conflict Detection Logic

JARVIS should check for these conflict types:

| Conflict Type | How to detect |
|---|---|
| Class vs Assignment due | `assignment.start` falls within 2 hours of `class.start` on same day |
| Back-to-back classes | Gap between `class1.end` and `class2.start` is less than 15 minutes |
| Assignment due during exam period | Cross-reference assignment dates with known exam weeks |
| Multiple deadlines same day | More than 2 assignments with same `start` date |

---

## Reminder Schedule

JARVIS should proactively remind students at these trigger points:

| Trigger | Reminder |
|---|---|
| 7 days before assignment due | "You have `<title>` due in 7 days" |
| 3 days before assignment due | "Urgent: `<title>` due in 3 days — have you started?" |
| 1 day before assignment due | "Final reminder: `<title>` is due tomorrow at `<time>`" |
| Morning of class day | "Today's classes: `<list>`" |
| Evening before | "Tomorrow you have `<class>` at `<time>` in `<location>`" |

---

## Error Handling

| Error | JARVIS response |
|---|---|
| ICS URL unreachable | "I couldn't reach your calendar right now. Please check your internet connection or re-share your calendar link." |
| Empty calendar | "Your calendar appears to be empty. Make sure you've shared the correct calendar feed." |
| Unsupported file type | "I can only read `.ics`, `.csv`, and `.xml` calendar files." |
| URL from untrusted host | "That calendar URL isn't from a supported source. Please use your QUT Timetable, Canvas, or Outlook calendar link." |

---

## Student Setup Instructions

Share these instructions with the student so they can connect their calendars:

### QUT Timetable
1. Go to [mytimetable.qut.edu.au](https://mytimetable.qut.edu.au)
2. Log in with your QUT credentials
3. Click the **Subscribe** or **Export** button
4. Copy the **ICS URL** and give it to JARVIS

### QUT Canvas
1. Go to [canvas.qut.edu.au](https://canvas.qut.edu.au) → **Calendar**
2. Scroll to the bottom right and click **Calendar Feed**
3. Copy the ICS URL and give it to JARVIS

### Outlook (QUT Email Calendar)
1. Go to [outlook.office.com](https://outlook.office.com) → **Calendar**
2. Settings → View all Outlook settings → Calendar → Shared Calendars
3. Publish your calendar and copy the **ICS link**

---

## Dependencies

```
fastapi
uvicorn
icalendar
python-multipart
requests
```

Install:
```bash
source /home/jarvis/Project/backend/venv/bin/activate
pip install fastapi uvicorn icalendar python-multipart requests
```

---

## File Location

```
AIML_Hackathon_Jarvis/
└── backend/
    └── src/
        └── calendar_parser.py    # The calendar parser module
```

Run locally:
```bash
python backend/src/calendar_parser.py
# API available at http://localhost:8001
# Docs available at http://localhost:8001/docs
```
