# 🗄️ JARVIS Skill — Supabase Database & Student Profile

## Skill Overview
This skill allows JARVIS to query the Supabase database to understand who the student is,
what they are studying, their assignments, stories, and study habits.
Once the database is populated during onboarding, JARVIS can personalise every response
based on real student data rather than asking the student to repeat themselves.

**Trigger phrases:**
- "Who am I?" / "What do you know about me?"
- "What are my subjects?"
- "What assignments do I have?"
- "How long have I studied today?"
- "What stories have I listened to?"
- "Where am I up to in my story?"
- Any question where JARVIS needs to know the student's name, degree, year, or preferences

---

## Database Connection

```python
import os
from supabase import create_client

SUPABASE_URL  = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY  = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")   # for student-facing queries
SERVICE_KEY   = os.getenv("SUPABASE_SERVICE_ROLE_KEY")        # for admin/backend queries

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
```

> Always use the **anon key** for student-facing queries — it respects Row Level Security (RLS).
> Only use the **service role key** for backend admin operations (e.g. seeding, migrations).

---

## Schema Reference

### Table 1 — `profiles`
The core identity table. Every student has one row here created during onboarding.
All other tables link back to this via `user_id`.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | uuid | NO | Primary key — matches `auth.users.id` |
| `name` | text | YES | Student's full name |
| `degree` | text | YES | Degree program e.g. "Bachelor of IT" |
| `year` | integer | YES | Year of study e.g. 1, 2, 3 |
| `dietary` | ARRAY | YES | Dietary preferences e.g. ["halal", "vegetarian"] |
| `subjects` | ARRAY | YES | Enrolled subjects e.g. ["CAB301", "IFB104"] |
| `character` | text | YES | Chosen JARVIS persona/character |
| `timetable_url` | text | YES | QUT MyTimetable ICS subscription URL |
| `created_at` | timestamptz | YES | Profile creation timestamp |
| `updated_at` | timestamptz | YES | Last profile update timestamp |

```python
def get_student_profile(user_id: str) -> dict:
    """Fetch the full student profile by user ID."""
    result = supabase.table("profiles") \
        .select("*") \
        .eq("id", user_id) \
        .single() \
        .execute()
    return result.data
```

**Example profile data:**
```json
{
  "id": "uuid-here",
  "name": "Hashim Hilal",
  "degree": "Bachelor of Information Technology",
  "year": 2,
  "dietary": ["halal"],
  "subjects": ["CAB301", "IFB104", "CAB202"],
  "character": "JARVIS",
  "timetable_url": "https://mytimetable.qut.edu.au/aplus/rest/calendar/ical/...",
  "created_at": "2026-04-11T00:00:00Z",
  "updated_at": "2026-04-11T00:00:00Z"
}
```

---

### Table 2 — `assignments`
Stores the student's Canvas assignments — either synced from the Canvas ICS feed
or manually added by the student.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | uuid | NO | Primary key |
| `user_id` | uuid | NO | FK → `profiles.id` |
| `title` | text | NO | Assignment title e.g. "CAB301 Assignment 1" |
| `subject` | text | YES | Subject code e.g. "CAB301" |
| `due_date` | date | YES | Due date |
| `completed` | boolean | YES | Whether the student has marked it done |
| `created_at` | timestamptz | YES | Record creation timestamp |

```python
from datetime import date

def get_upcoming_assignments(user_id: str) -> list[dict]:
    """Fetch all incomplete assignments due from today onwards."""
    result = supabase.table("assignments") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("completed", False) \
        .gte("due_date", date.today().isoformat()) \
        .order("due_date", desc=False) \
        .execute()
    return result.data

def mark_assignment_complete(assignment_id: str) -> dict:
    """Mark an assignment as completed."""
    result = supabase.table("assignments") \
        .update({"completed": True}) \
        .eq("id", assignment_id) \
        .execute()
    return result.data

def get_overdue_assignments(user_id: str) -> list[dict]:
    """Fetch all incomplete assignments past their due date."""
    result = supabase.table("assignments") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("completed", False) \
        .lt("due_date", date.today().isoformat()) \
        .order("due_date", desc=False) \
        .execute()
    return result.data
```

---

### Table 3 — `stories`
Stores bedtime stories — both AI-generated custom stories and the public shared library.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | uuid | NO | Primary key |
| `user_id` | uuid | YES | FK → `profiles.id` (null = system story) |
| `title` | text | NO | Story title |
| `author` | text | YES | Author name or "JARVIS" |
| `content` | text | YES | Full story text |
| `audio_url` | text | YES | URL to narration audio file |
| `cover_url` | text | YES | URL to story cover image |
| `duration_seconds` | integer | YES | Narration duration in seconds |
| `is_custom` | boolean | YES | True = AI generated for this student |
| `is_public` | boolean | YES | True = visible to all students |
| `created_at` | timestamptz | YES | Story creation timestamp |

```python
def get_public_stories() -> list[dict]:
    """Fetch all publicly available stories."""
    result = supabase.table("stories") \
        .select("id, title, author, duration_seconds, cover_url") \
        .eq("is_public", True) \
        .order("created_at", desc=True) \
        .execute()
    return result.data

def get_student_custom_stories(user_id: str) -> list[dict]:
    """Fetch all custom stories generated for this student."""
    result = supabase.table("stories") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("is_custom", True) \
        .order("created_at", desc=True) \
        .execute()
    return result.data
```

---

### Table 4 — `story_progress`
Tracks how far each student has listened through each story.
Uses a composite primary key of `user_id + story_id` — one progress record per student per story.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `user_id` | uuid | NO | FK → `profiles.id` (part of PK) |
| `story_id` | uuid | NO | FK → `stories.id` (part of PK) |
| `position_seconds` | integer | YES | Playback position in seconds |
| `completed` | boolean | YES | Whether the student finished the story |
| `last_played` | timestamptz | YES | When they last played this story |

```python
def get_story_progress(user_id: str, story_id: str) -> dict | None:
    """Get playback progress for a specific story."""
    result = supabase.table("story_progress") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("story_id", story_id) \
        .single() \
        .execute()
    return result.data

def upsert_story_progress(user_id: str, story_id: str, position_seconds: int, completed: bool = False):
    """Save or update playback position."""
    from datetime import datetime, timezone
    result = supabase.table("story_progress") \
        .upsert({
            "user_id": user_id,
            "story_id": story_id,
            "position_seconds": position_seconds,
            "completed": completed,
            "last_played": datetime.now(timezone.utc).isoformat()
        }) \
        .execute()
    return result.data

def get_recently_played(user_id: str) -> list[dict]:
    """Get stories the student has recently played, with progress."""
    result = supabase.table("story_progress") \
        .select("*, stories(title, author, duration_seconds, cover_url)") \
        .eq("user_id", user_id) \
        .order("last_played", desc=True) \
        .limit(5) \
        .execute()
    return result.data
```

---

### Table 5 — `study_sessions`
Tracks each study session logged by the student — subject, duration, and date.
JARVIS uses this to understand study patterns and make scheduling suggestions.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | uuid | NO | Primary key |
| `user_id` | uuid | NO | FK → `profiles.id` |
| `subject` | text | NO | Subject code e.g. "CAB301" |
| `duration_minutes` | integer | NO | How long the session lasted |
| `date` | date | YES | Date of the study session |
| `created_at` | timestamptz | YES | Record creation timestamp |

```python
def get_study_sessions(user_id: str, days: int = 7) -> list[dict]:
    """Fetch study sessions from the last N days."""
    from datetime import date, timedelta
    since = (date.today() - timedelta(days=days)).isoformat()
    result = supabase.table("study_sessions") \
        .select("*") \
        .eq("user_id", user_id) \
        .gte("date", since) \
        .order("date", desc=True) \
        .execute()
    return result.data

def get_study_summary(user_id: str) -> dict:
    """Summarise total study minutes per subject in the last 7 days."""
    sessions = get_study_sessions(user_id, days=7)
    summary = {}
    for s in sessions:
        subject = s["subject"]
        summary[subject] = summary.get(subject, 0) + s["duration_minutes"]
    return summary

def log_study_session(user_id: str, subject: str, duration_minutes: int) -> dict:
    """Log a new study session."""
    from datetime import date
    result = supabase.table("study_sessions") \
        .insert({
            "user_id": user_id,
            "subject": subject,
            "duration_minutes": duration_minutes,
            "date": date.today().isoformat()
        }) \
        .execute()
    return result.data
```

---

## JARVIS Student Context Builder

This is the most important function in this skill. Call it at the start of every conversation
to build a complete picture of the student before responding.

```python
import json
from datetime import date, timedelta

def build_student_context(user_id: str) -> dict:
    """
    Fetch all student data from Supabase and return a unified
    context object ready to be injected into the JARVIS prompt.
    """
    profile     = get_student_profile(user_id)
    assignments = get_upcoming_assignments(user_id)
    overdue     = get_overdue_assignments(user_id)
    study_sum   = get_study_summary(user_id)
    recent_stor = get_recently_played(user_id)

    return {
        "student": {
            "name":         profile.get("name"),
            "degree":       profile.get("degree"),
            "year":         profile.get("year"),
            "subjects":     profile.get("subjects", []),
            "dietary":      profile.get("dietary", []),
            "character":    profile.get("character", "JARVIS"),
            "timetable_url": profile.get("timetable_url"),
        },
        "assignments": {
            "upcoming": assignments,
            "overdue":  overdue,
            "total_pending": len(assignments) + len(overdue)
        },
        "study": {
            "last_7_days_by_subject": study_sum,
            "total_minutes_this_week": sum(study_sum.values())
        },
        "stories": {
            "recently_played": recent_stor
        },
        "today": date.today().isoformat()
    }


def build_jarvis_prompt(user_id: str, user_query: str) -> str:
    """
    Build a fully personalised JARVIS system prompt
    using live data from Supabase.
    """
    ctx = build_student_context(user_id)
    s   = ctx["student"]

    return f"""You are {s['character']}, an intelligent personal AI assistant for a QUT university student.

## WHO YOU ARE TALKING TO
- Name      : {s['name']}
- Degree    : {s['degree']} (Year {s['year']})
- Subjects  : {', '.join(s['subjects']) if s['subjects'] else 'Not set'}
- Dietary   : {', '.join(s['dietary']) if s['dietary'] else 'No preferences set'}
- Today     : {ctx['today']}

## ASSIGNMENTS
Upcoming ({len(ctx['assignments']['upcoming'])} pending):
{json.dumps(ctx['assignments']['upcoming'], indent=2, default=str)}

Overdue ({len(ctx['assignments']['overdue'])} overdue):
{json.dumps(ctx['assignments']['overdue'], indent=2, default=str)}

## STUDY THIS WEEK
{json.dumps(ctx['study']['last_7_days_by_subject'], indent=2)}
Total: {ctx['study']['total_minutes_this_week']} minutes this week

## RECENTLY PLAYED STORIES
{json.dumps(ctx['stories']['recently_played'], indent=2, default=str)}

## STUDENT'S MESSAGE
{user_query}

## YOUR BEHAVIOUR
- Address the student by their first name: {s['name'].split()[0] if s['name'] else 'there'}
- Be concise, warm, and proactive
- Flag overdue assignments immediately if relevant
- Suggest study sessions based on their weekly pattern
- Use Brisbane time (AEST) for all times and dates
- If the student asks about their timetable, use the calendar skill with their timetable_url
"""
```

---

## Table Relationships

```
profiles (id)
    │
    ├──── assignments  (user_id → profiles.id)
    ├──── stories      (user_id → profiles.id)
    ├──── story_progress (user_id → profiles.id)
    │         └── stories (story_id → stories.id)
    └──── study_sessions (user_id → profiles.id)
```

---

## JARVIS Response Examples

**Student:** "What do I have due this week?"
```
JARVIS fetches: get_upcoming_assignments(user_id)
Filters: due_date within next 7 days
Responds: "Hi Hashim! You have 2 assignments due this week:
  - CAB301 Assignment 2 — due Thursday 14 April
  - IFB104 Project — due Friday 15 April
  You haven't started logging study for CAB301 this week — want me to set a reminder?"
```

**Student:** "How much have I studied this week?"
```
JARVIS fetches: get_study_summary(user_id)
Responds: "This week you've studied:
  - CAB301: 120 minutes
  - IFB104: 90 minutes
  Total: 210 minutes (3.5 hours). Your CAB202 hasn't had any sessions yet this week."
```

**Student:** "Continue my story"
```
JARVIS fetches: get_recently_played(user_id)[0]
Gets: position_seconds = 342, story title = "The Enchanted Forest"
Responds: "Resuming 'The Enchanted Forest' from 5 minutes 42 seconds. Sweet dreams, Hashim."
```

---

## Recommended Future Schema Additions

These columns/tables would make JARVIS even smarter:

| Addition | Why |
|---|---|
| `profiles.canvas_url` | Separate Canvas ICS URL from timetable URL |
| `assignments.canvas_event_id` | Prevent duplicates when syncing from Canvas ICS |
| `assignments.reminder_sent` | Track whether JARVIS has already sent a reminder |
| `profiles.openai_thread_id` | Persist conversation history per student |
| `notifications` table | Log all reminders JARVIS has sent |
| `meal_preferences` table | For the Meal Buddy feature |

---

## File Location

```
AIML_Hackathon_Jarvis/
└── llmops/
    └── skills/
        └── SUPABASE_SCHEMA_SKILL.md
```

*Schema source: Supabase project — eredinmxmdlgeqfmgtsm.supabase.co*
*Last updated: April 2026*
