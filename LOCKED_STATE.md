# JARVIS — Locked State Snapshot

**Last updated:** 2026-04-12
**Status:** Voice-to-voice working. Calendar/Event page working. Subjects (RAG chat) working. **Meal & Friends (dining matchmaker) working with user-to-user match verified at 80% compatibility.**

This file documents every moving part of the working configuration so nothing
gets accidentally broken. If something stops working, diff against the file
paths below and restore the behavior described here.

---

## End-to-end verified flows

### 1. Calendar sync (Event admin page)
- User signs in at `/login` with Supabase Auth email+password
- `/` shows the admin home (sidebar: Home / Jarvis / Event)
- `/event` loads the QUT Timetable + Canvas URL form, pre-filled from the user's `profiles` row
- "Sync Now" hits `POST /api/admin/sync` → backend reads `profiles.qut_timetable_ics_url` and `profiles.qut_canvas_ics_url`, fetches ICS feeds, parses via the existing `routes/calendar_parser.py` helpers, and upserts 100+ events into the `events` table scoped to the signed-in user
- Calendar month grid renders events with color-coded chips (cyan for classes, orange for assignments)
- "Upcoming" list shows next 14 days
- Auto-sync fires on page mount when `last_calendar_sync_at` is older than 5 minutes

### 2. Chat with real calendar tool-use (`/jarvis` text box, also reachable from voice UI)
- Frontend sends `POST /api/chat` with Authorization: Bearer <supabase_access_token>
- Backend extracts user_id via optional auth dependency
- Claude (claude-sonnet-4-6) runs the full N-turn tool-use loop (up to 5 turns)
- `get_upcoming_events`, `create_event`, `cancel_event`, `sync_calendar_feed` are wired to real Supabase queries scoped to the user
- Other tools (`set_reminder`, `get_campus_directions`, `get_cafeteria_menu`) stay stubbed and clearly labeled
- Verified response: asking "what do I have coming up this week?" returns real class/assignment titles with Brisbane times

### 3. Voice-to-voice via OpenAI Realtime API (`⚡ LIVE` button on `/jarvis`)
- Frontend calls `POST /api/realtime/session` to mint a GA client secret (`ek_*`)
- `useRealtime.js` enumerates audio input devices and picks the first non-virtual one (skips BlackHole, Loopback, Soundflower, Aggregate, Multi-Output, iShowU, Rogue Amoeba, VB-Audio, Voicemeeter, OBS)
- Calls `getUserMedia({audio: {deviceId: {exact: ...}}})` with explicit physical mic
- Creates `RTCPeerConnection`, adds track, creates SDP offer
- POSTs SDP offer to `https://api.openai.com/v1/realtime/calls?model=gpt-realtime` (GA endpoint — NOT `/v1/realtime`, which is beta and rejects GA secrets)
- Sets SDP answer, data channel opens, ontrack fires, `audioEl.play()` resolves
- Sage's voice streams back over WebRTC peer connection directly (audio bytes never touch our backend)
- Verified response: "Hey! How's it going? What can I help you with today?"

### 4. Subjects (course helper) — verified end-to-end
- User creates a subject with name/code/term/color
- Uploads syllabus / rubric / module text (paste text OR file upload); `material_extraction` runs pypdf for PDFs and Claude Vision for images
- Extracted text goes into `subject_materials.content_text`; raw files land in Supabase Storage bucket `course-materials` at `user_id/subject_id/material_id.ext`
- Subject detail page has tabs (Syllabus / Modules / Assignments / Rubrics / Files / Notes) + a sticky right-side chat panel
- Chat panel POSTs `/api/chat` with `subject_id`; backend injects `build_subject_context(subject_id, user_id)` dossier into Claude's system prompt alongside the meal buddy dossier
- Verified cross-material reasoning: asking about assignment 2 pulled points from the uploaded rubric AND the weight % from the syllabus

### 5. Meal & Friends (dining matchmaker) — verified user-to-user match at 80% compatibility
- User configures dining preferences at `/meal-buddy/preferences`: cuisines (italian/japanese/thai/...), budget amount + tier ($/$$/$$$), dietary flags (vegetarian/vegan/gluten_free/halal/...)
- Browses trending Hot List + full catalogue at `/meal-buddy/discover`, picks up to 3 favourite eateries (server-enforced limit of 3)
- Marks free slots on the 7-day × 4-slot grid at `/meal-buddy/availability` (11:30/12:30/18:00/19:00)
- Proposes a match with another user via the `+ PROPOSE MATCH` modal on `/meal-buddy/matches` (or asks Jarvis to do it)
- Backend auto-computes compatibility via `_compute_compatibility()` — cuisine overlap (max 40) + dietary compat (max 30) + budget tier fit (max 20) + picks overlap bonus (max 10)
- Other user sees the pending proposal, clicks Accept/Decline; when both `a_response` and `b_response` are 'accepted', status flips to `accepted`
- **Verified test:** User A (karolbhandari78@gmail.com) + User B (jarvis-buddy-xxx@jarvis.test, created via admin API). Both set overlapping cuisines and Sushi Zen in picks. User A proposed lunch at Sushi Zen; score computed at **80%** with factors `{cuisine_align:30, dietary_comp:20, budget_fit:20, picks_overlap:10}`. User B accepted; both sides now see `status='accepted'`.

---

## Files that MUST NOT be silently edited

### Backend (`/Users/karolbhandari/jarvis-recovered/backend/`)

| File | Role |
|---|---|
| `src/main.py` | Mounts **7 routers** (calendar_parser, voice, chat, admin, realtime, subjects, meal_buddy) + CORS + dotenv + access log middleware. |
| `src/supabase_client.py` | Singleton Supabase client from `SUPABASE_SERVICE_ROLE_KEY`. |
| `src/auth.py` | `get_current_user_id` dep — calls Supabase `/auth/v1/user` to validate bearer token. |
| `src/services/calendar_sync.py` | `sync_user_feeds(user_id)` — reuses calendar_parser helpers; delete-then-insert upsert strategy per source. |
| `src/services/storage.py` | Supabase Storage helper for the `course-materials` bucket. Lazy `ensure_bucket()`, partitioned path `user_id/subject_id/material_id.ext`, signed URL generator. |
| `src/services/material_extraction.py` | Text extractor for uploaded course materials: pypdf for PDFs, Claude Vision (`claude-sonnet-4-6`) for images, passthrough for plain text. Truncates at 60 000 chars. |
| `src/routes/admin.py` | Router prefix `/api/admin`. `GET/PUT /feeds`, `POST /sync`, `GET/POST /events`, `DELETE /events/{id}`. Depends on `get_current_user_id`. |
| `src/routes/realtime.py` | Router prefix `/api/realtime`. `POST /session` mints OpenAI Realtime client secret + **optionally accepts Authorization Bearer** to inject the user's Meal & Friends dossier into session instructions. `POST /debug` receives client-side breadcrumbs → `/tmp/jarvis_client_debug.log`. |
| `src/services/realtime_voice.py` | Calls `https://api.openai.com/v1/realtime/client_secrets` with config from `openai_speech_to_speech.json`. **DEFAULT_MODEL = "gpt-realtime"** (GA). Do NOT switch to `gpt-4o-realtime-preview-*` — that's beta and won't work with the GA secret the endpoint returns. `REALTIME_TOOLS` list has **15 function definitions** (3 calendar + 12 meal buddy); `build_session_config(user_id=...)` injects Brisbane time + meal buddy dossier. |
| `src/routes/chat.py` | Claude chat with full tool-use loop. Optional Bearer token auth. **Tools list has 18 definitions** — 7 calendar + 9 meal buddy + 2 stubs. Auto-injects both `build_meal_buddy_context` and `build_subject_context` (if `subject_id` present) into system prompt. |
| `src/routes/subjects.py` | Router prefix `/api/subjects`. CRUD for subjects + subject_materials (text + file upload). Signed URLs for files. Includes `build_subject_context()` used by chat.py. Returns **412 `schema_not_ready`** when the tables don't exist yet. |
| `src/routes/meal_buddy.py` | Router prefix `/api/meal-buddy`. CRUD for all 6 tables + eatery auto-seed on first `GET /eateries` (10 restaurants from the mockups) + `_compute_compatibility()` scoring + `build_meal_buddy_context()` used by chat.py AND realtime_voice.py. Returns **412 `schema_not_ready`** when the tables don't exist yet. |
| `config/openai_speech_to_speech.json` | Session template: `model="gpt-realtime"`, `voice="sage"`, instructions grounding JARVIS in the user's calendar. |
| `sql/001_subjects.sql` | One-time migration for `subjects` + `subject_materials` tables + shared `touch_updated_at()` function. |
| `sql/002_meal_buddy.sql` | One-time migration for 6 meal buddy tables (`dining_preferences`, `eateries`, `dining_picks`, `dining_availability`, `meal_matches`, `dining_stats`) + their triggers. Reuses `touch_updated_at()` from 001. |
| `.venv/` | Python 3.11 venv with all deps from `requirements.txt` installed (includes `pypdf`). Do not delete. |

### Frontend (`/Users/karolbhandari/jarvis-recovered/frontend/`)

| File | Role |
|---|---|
| `src/App.jsx` | Renders `<AppRouter />`. One-liner. |
| `src/AppRouter.jsx` | BrowserRouter + AuthProvider. Routes: `/login`, `/` (HomePage), `/jarvis` (JarvisShell), `/event` (AdminShell), `/subjects`, `/subjects/:subjectId`, `/meal-buddy`, `/meal-buddy/preferences`, `/meal-buddy/discover`, `/meal-buddy/availability`, `/meal-buddy/matches`. |
| `src/AuthProvider.jsx` | Supabase session context. |
| `src/lib/supabase.js` | Browser Supabase client with resilient storage adapter (falls back to memory on `QuotaExceededError`). **Storage key: `jarvis-admin-auth`**. |
| `src/lib/api.js` | `authedFetch` helper + typed wrappers for `/api/admin/*`, `/api/subjects/*`, and `/api/meal-buddy/*`. Preserves structured error bodies on 412 so setup banners can detect `schema_not_ready`. |
| `src/layouts/AdminShell.jsx` | Sidebar + `<Outlet/>`. Sidebar has **5 items** (Home / Jarvis / Event / Subjects / Meal & Friends). Toggles `body.style.overflow='auto'` on mount. |
| `src/layouts/JarvisShell.jsx` | Full-bleed wrapper + floating ← ADMIN pill for `/jarvis`. |
| `src/pages/HomePage.jsx` | Landing cards (Jarvis / Event / Subjects / Meal & Friends). |
| `src/pages/LoginPage.jsx` | Supabase email+password. |
| `src/pages/EventPage.jsx` | Month calendar + feed form + upcoming list + manual event create. Auto-sync on mount. |
| `src/pages/JarvisPage.jsx` | One-liner wrapper: `return <JarvisCanvas />`. |
| `src/pages/SubjectsListPage.jsx` | Subject list + create modal. Detects 412 and shows setup banner. |
| `src/pages/SubjectDetailPage.jsx` | Tabs (syllabus/modules/rubrics/files/notes) + side chat pane. |
| `src/pages/MealBuddyHub.jsx` | Dashboard with stats strip + 4 cards linking to the sub-pages. |
| `src/pages/DiningPreferencesPage.jsx` | Cuisine chips + budget slider/tier + dietary pills + save button. |
| `src/pages/DiscoverPage.jsx` | Horizontal "Hot List" + catalogue grid. Click-to-pick, max 3 enforced server-side. |
| `src/pages/AvailabilityPage.jsx` | 7×4 weekly schedule grid. Tap cycles empty → lunch → dinner → empty. |
| `src/pages/MatchesPage.jsx` | Match list + `ProposeMatchModal` (user picker + eatery picker + datetime) + Accept/Decline buttons. |
| `src/components/Calendar.jsx` | Custom month grid. **Uses `repeat(7, minmax(0, 1fr))`** — do NOT change to `1fr` alone, that causes chip overflow. |
| `src/components/FeedForm.jsx` | QUT URL inputs + Save / Sync Now buttons. |
| `src/components/EventList.jsx` | Upcoming events list grouped by day. |
| `src/components/JarvisCanvas.jsx` | The voice UI. Now includes useRealtime + useWakeWord integration. Legacy useVoice auto-start is intentionally REMOVED — do not re-add it or the mic will conflict. |
| `src/components/MaterialUploader.jsx` | Text + file + paste-screenshot uploader for subject materials. |
| `src/components/MaterialList.jsx` | Expandable material list with signed-URL Open button and delete. |
| `src/components/SubjectChat.jsx` | Streaming chat pane on the subject detail page. Sends `subject_id` to `/api/chat`. |
| `src/components/MealBuddyNav.jsx` | **Sticky sub-nav tab bar** rendered at the top of all `/meal-buddy/*` pages. 5 tabs: Hub / Preferences / Discover / Availability / Matches. |
| `src/components/MealBuddySetupBanner.jsx` | Setup banner for `/meal-buddy/*` when the backend returns 412 schema_not_ready. Copies `sql/002_meal_buddy.sql` to clipboard. |
| `src/hooks/useEvents.js` | useEvents({from,to}) → fetch + cache. |
| `src/hooks/useJarvis.js` | `/api/chat` caller. **Attaches Supabase JWT as Authorization header** — required for chat tool-use to scope to the right user. |
| `src/hooks/useVoice.js` | Legacy request/response STT+TTS. Unchanged from pre-lock state. |
| `src/hooks/useRealtime.js` | **CRITICAL**. WebRTC Realtime hook. Five things that must NOT change: (1) `OPENAI_REALTIME_URL = 'https://api.openai.com/v1/realtime/calls'` (GA endpoint), (2) device enumeration + virtual-device filter, (3) explicit `deviceId: {exact: ...}` constraint in getUserMedia, (4) debug breadcrumbs to `/api/realtime/debug`, (5) **forwards Supabase JWT to `/api/realtime/session`** so the backend can inject the meal buddy dossier into Sage's session instructions at mint time. Tool executor has 12 meal buddy branches + 3 calendar branches. |
| `src/hooks/useWakeWord.js` | "Hey JARVIS" detector via Web Speech API. Fires onWake from onend (not onresult) so the mic is fully released before the caller reacquires it. Verbose logging defaults to false after lock. |
| `.env.local` | `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`. Do NOT add `sb_secret_*` here. |
| `vite.config.js` | `/api` and (optionally) `/calendar` proxied to `http://localhost:8000` **WITHOUT rewrite**. Router prefixes in FastAPI must match the frontend URLs verbatim. |
| `package.json` | Pinned deps: `react-router-dom@^7`, `@supabase/supabase-js@^2`, React 19, Vite 8, Tailwind 4. |

### Config

| File | Role |
|---|---|
| `/Users/karolbhandari/jarvis-recovered/.env` | Backend-only secrets: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`. |
| `/Users/karolbhandari/Documents/Demo /sample-demo/.claude/worktrees/eager-bose/.claude/launch.json` | preview_start config for `jarvis-backend` and `jarvis-frontend`, pointing at `/Users/karolbhandari/jarvis-recovered/backend` and `frontend`. |

### Runtime logs (tailable for debugging)

| Path | Role |
|---|---|
| `/tmp/jarvis_access.log` | Every HTTP request to the backend (written by middleware in `main.py`). |
| `/tmp/jarvis_client_debug.log` | Client-side WebRTC breadcrumbs posted from `useRealtime.js` → `POST /api/realtime/debug`. |

---

## Critical invariants — do not break these

1. **OpenAI Realtime SDP endpoint is `/v1/realtime/calls` (GA)**, not `/v1/realtime` (beta). A GA client secret (`ek_*`) posted to the beta endpoint returns `api_version_mismatch`.
2. **Model is `gpt-realtime`**, not `gpt-4o-realtime-preview-*`. Beta models don't work with GA secrets.
3. **Voice is `sage`**. Defined in `backend/config/openai_speech_to_speech.json`.
4. **Device filter regex:** `/blackhole|loopback|soundflower|virtual|aggregate|multi-?output|iShowU|rogue amoeba|vb-audio|voicemeeter|obs/i` — skips all known virtual audio drivers so `getUserMedia` lands on a real mic even if the user's system default is BlackHole.
5. **Vite proxy has NO rewrite.** `/api/admin/feeds` goes to the backend as `/api/admin/feeds`. All routers in `backend/src/routes/*.py` MUST use the full `/api/*` prefix.
6. **CORS** in `main.py` is `allow_origins=["*"]` + `allow_credentials=True`. This combo is technically invalid for cross-origin credentialed requests, but everything here runs same-origin via the Vite proxy so it never hits the browser's check. Do NOT change it unless you're also changing the proxy topology.
7. **Supabase session key** in `lib/supabase.js` is `jarvis-admin-auth`. Renamed from the default `sb-*` key to dodge a stale `QuotaExceededError` Atlas hit earlier.
8. **`useVoice` does NOT auto-start on mount.** The old behavior was `useEffect(() => startListening(), [])`. It caused mic conflicts with Realtime. Do not re-add.
9. **`chat.py` `MAX_TOOL_TURNS = 5`.** Prevents Claude tool-use loops from running away.
10. **Tool-result blocks in `chat.py`** use `content: json.dumps(result)` — they must be strings in the Anthropic API, not raw objects.
11. **`chat.py` injects TWO dossiers into the system prompt:** `build_meal_buddy_context` (always, when signed in) + `build_subject_context` (only when `subject_id` is on the request). Order matters — meal buddy first, subjects second. Do NOT remove either.
12. **`/api/realtime/session` is _optionally_ authenticated** (reads `Authorization: Bearer …` via `_optional_user_id`). When a valid token is present, `create_client_secret(user_id=…)` bakes the meal buddy dossier into the Realtime session instructions. `useRealtime.js` MUST forward the Supabase JWT on every `session` mint, otherwise Sage starts every conversation cold.
13. **Realtime tools = 20 total.** 3 calendar (`create_event`, `get_upcoming_events`, `cancel_event`) + 12 meal buddy (`list_eateries`, `get_meal_preferences`, `update_meal_preferences`, `get_meal_picks`, `add_meal_pick`, `remove_meal_pick`, `set_dining_availability`, `clear_dining_availability`, `list_meal_matches`, `respond_to_meal_match`, `propose_meal_match`, `list_other_users_for_match`) + 5 subject (`list_subjects`, `get_subject_context`, `search_subject_materials`, `create_subject`, `add_subject_material_text`). Every tool name in `REALTIME_TOOLS` in `realtime_voice.py` **must** have a matching branch in `useRealtime.js::executeRealtimeTool`, otherwise Sage will call it and the hook will reply `unknown_tool`.
14. **Claude text chat tools = 21 total** (3 calendar + 1 sync + 9 meal buddy + 5 subject + 2 stubs + 1 reminder). Every `TOOL_HANDLERS` dict entry must match a tool definition in `TOOLS`.
14a. **Chat `chat.py` injects THREE dossiers** into the system prompt for every authed request: `build_meal_buddy_context(user_id)` + `build_subjects_summary(user_id)` + (if `subject_id` is present) `build_subject_context(subject_id, user_id)`. Order is meal → subjects list → subject detail. Do NOT remove any of them.
14b. **Realtime `build_session_config(user_id=...)` injects TWO dossiers** into the session instructions: meal buddy dossier (`_meal_buddy_dossier_for_session`) + subjects summary (`_subjects_summary_for_session`). Both are late-imported from `src.routes.*` to avoid circular imports.
15. **Meal buddy `compatibility_score` lives in 0–100.** The CHECK constraint on `meal_matches.compatibility_score` enforces it. If you rewrite `_compute_compatibility`, clamp the result to `max(0, min(100, total))` or Postgres will reject the insert.
16. **Match acceptance is symmetric.** `status` only flips to `accepted` when **both** `a_response` AND `b_response` are `'accepted'`. A single-side accept leaves it in `proposed`. A single `declined` from either side immediately flips to `declined`. See `respond_to_match` in `meal_buddy.py`.
17. **Eatery seeds are idempotent at the PROCESS level, not the DB level.** `_seeded_ref["done"]` is an in-memory flag. After a backend restart, the first `GET /eateries` call re-checks the table; if it's empty, it re-seeds. So deleting eateries in the DB and restarting the backend WILL re-seed them. Intentional.
18. **Eatery `price_tier` CHECK constraint allows only `'$'`, `'$$'`, `'$$$'`.** Same for `dining_preferences.budget_tier`. Frontend dropdowns must use the exact same strings.
19. **The `touch_updated_at()` Postgres function** is created by `001_subjects.sql` and *reused* by `002_meal_buddy.sql`. Do NOT drop it unless you're also dropping all triggers that reference it.
20. **Migration order matters.** Run `001_subjects.sql` BEFORE `002_meal_buddy.sql` — the latter's triggers reference the former's function.

---

## Environment prerequisites (macOS)

- **System Settings → Sound → Input:** should be a physical mic (MacBook Pro Microphone, USB mic, etc.). If it's BlackHole, the device filter in `useRealtime.js` auto-rescues `getUserMedia`, but `webkitSpeechRecognition` (wake word) does NOT support device constraints and will still hear silence. Change the system default for wake word to work.
- **System Settings → Sound → Output:** must NOT be BlackHole, Loopback, or a Multi-Output/Aggregate that includes one. Sage's audio streams back through WebRTC and plays through whatever macOS considers the default output. If that's a virtual sink, you hear silence.
- **OS-level mic permission:** System Settings → Privacy & Security → Microphone → the browser must be toggled ON.
- **Browser mic permission:** Chrome / Atlas address bar → 🔒 icon → Microphone → Allow (for localhost:5173).
- **Supabase dashboard:** Auth → Providers → Email enabled, "Confirm email" OFF for the hackathon demo. Auth → URL Configuration → Site URL: `http://localhost:5173`.

---

## How to run from scratch

```bash
# Backend
cd /Users/karolbhandari/jarvis-recovered/backend
source .venv/bin/activate
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend (separate terminal)
cd /Users/karolbhandari/jarvis-recovered/frontend
npm run dev -- --port 5173 --host 127.0.0.1
```

Or from Claude Code: `preview_start name="jarvis-backend"` / `preview_start name="jarvis-frontend"`.

---

## How to verify the voice pipeline end-to-end in 90 seconds

1. Open `http://localhost:5173/jarvis` in real Chrome (not Atlas — Atlas has known webkitSpeechRecognition issues for wake word but the LIVE button works).
2. Click `⚡ LIVE`. Grant mic permission if prompted.
3. Wait for button to say `🟢 LIVE — TAP TO END`.
4. Say: "Hey Jarvis, what do I have on Monday?"
5. Sage should reply in her voice within ~300ms.
6. Tap the button to disconnect.

If it fails:
- Click the `🔬 DIAG` chip in the bottom-left to reveal the diagnostic panel.
- Click TEST MIC to verify raw `getUserMedia`.
- Click COPY DIAG and paste the output to investigate.
- Tail `/tmp/jarvis_client_debug.log` for the full breadcrumb trace.

---

*Locked by Claude. Do not edit without reading the critical invariants above.*
