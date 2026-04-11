# JARVIS — Setup Guide

Full steps to clone `Stage-main` and run JARVIS locally on a fresh machine.

First run is **clone → configure two `.env` files → run SQL → `./scripts/start-dev.sh`**. After that, every subsequent launch is just the script.

---

## 0. Prerequisites

Install these once:

| Tool | Version | Check |
|---|---|---|
| Python | 3.11+ | `python3 --version` |
| Node.js | 20+ | `node --version` |
| npm | 10+ | `npm --version` |
| git | any | `git --version` |

You also need:

- A **Supabase** project (free tier is enough) — https://supabase.com/dashboard
- An **Anthropic** API key — https://console.anthropic.com
- An **OpenAI** API key with Realtime access — https://platform.openai.com/api-keys

---

## 1. Clone the repo

```bash
git clone -b Stage-main https://github.com/HashimHilal-QUT/AIML_Hackathon_Jarvis.git jarvis
cd jarvis
```

All commands in this guide run from the repo root (`jarvis/`) unless stated otherwise.

---

## 2. Create a Supabase project

1. Go to https://supabase.com/dashboard → **New project**.
2. Pick a region close to you. Wait ~2 min for provisioning.
3. In the left nav, go to **Project Settings → API** and copy three values:
   - **Project URL** (e.g. `https://abcd1234.supabase.co`)
   - `anon` **public** key (starts with `eyJ...`)
   - `service_role` **secret** key (also starts with `eyJ...`) — backend only, never ship to a browser

Keep this tab open; you'll paste these into the `.env` files in step 4.

### Enable email auth

Left nav → **Authentication → Providers → Email**:
- **Enable Email provider**: ON
- **Confirm email**: OFF (dev convenience — turn back on for production)

Left nav → **Authentication → URL Configuration**:
- **Site URL**: `http://localhost:5173`
- **Redirect URLs**: add `http://127.0.0.1:5173`

---

## 3. Run the SQL migrations

Left nav → **SQL Editor → New query**. Run each file's contents **in order**, one at a time (copy-paste, click **Run**):

1. `backend/sql/000_base.sql` — creates `profiles`, `events`, the new-user signup trigger, and the `course-materials` storage bucket.
2. `backend/sql/001_subjects.sql` — creates `subjects`, `subject_materials`, and the shared `touch_updated_at()` trigger.
3. `backend/sql/002_meal_buddy.sql` — creates the six Meal & Friends tables.

After each run you should see **Success. No rows returned** at the bottom. If a later migration complains about a missing table, re-run the earlier one.

---

## 4. Configure environment variables

Two files need to be created from the committed examples. Neither is tracked by git.

### Backend

```bash
cp backend/.env.example .env
```

Open `.env` and paste in the values from Supabase (step 2) plus your Anthropic + OpenAI keys:

```dotenv
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-proj-...
SUPABASE_URL=https://abcd1234.supabase.co
SUPABASE_ANON_KEY=eyJ...          # the anon public key
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # the service_role secret key
```

> The backend loads `.env` from the **repo root** first, then falls back to `backend/.env`. Using the repo-root path means you only have one file to edit.

### Frontend

```bash
cp frontend/.env.example frontend/.env.local
```

Open `frontend/.env.local` and paste in the same Supabase URL + the **anon** key (not the service role):

```dotenv
VITE_SUPABASE_URL=https://abcd1234.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...     # same anon key as above
VITE_BACKEND_URL=
```

Leave `VITE_BACKEND_URL` empty — the Vite dev proxy forwards `/api/*` to `http://127.0.0.1:8000` automatically.

---

## 5. Install dependencies

### Backend (one-time)

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install --upgrade pip
backend/.venv/bin/pip install -r backend/requirements.txt
```

### Frontend (one-time)

```bash
cd frontend
npm install
cd ..
```

---

## 6. Run it

```bash
./scripts/start-dev.sh
```

You should see:

```
[start-dev] starting backend on http://127.0.0.1:8000
[start-dev] starting frontend on http://127.0.0.1:5173
============================================================
  JARVIS is starting up
  Backend:  http://127.0.0.1:8000/health
  Frontend: http://127.0.0.1:5173
  Logs:     streamed below — Ctrl-C to stop both processes
============================================================
```

Open http://127.0.0.1:5173 in a browser (Chrome recommended for WebRTC voice).

Ctrl-C once in the terminal to stop both services.

---

## 7. First-run smoke test

1. You should land on `/login`.
2. Click **Create Account**, enter any email + password ≥ 6 chars.
3. You should be redirected to `/` (the admin home) — you now have a `profiles` row.
4. Navigate to **/event** and try the manual "Add event" form. The event should appear on the calendar.
5. Navigate to **/subjects** and create a subject.
6. Navigate to **/meal-buddy** and set a dining preference.
7. Click the glowing JARVIS orb (top-right or `/jarvis` link), allow mic access, and say "What do I have tomorrow?" — Claude should respond with your real events.

If any of those fail, check the backend logs in the terminal and the browser DevTools console.

---

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| `401 Unauthorized` on `/api/admin/*` | Frontend isn't sending the Supabase JWT. Sign out and back in. |
| `412 schema_not_ready` | A migration didn't run. Re-run `000_base.sql` → `001_subjects.sql` → `002_meal_buddy.sql` in order. |
| Backend crashes on startup with `SUPABASE_URL missing` | The `.env` file isn't at the repo root, or one of the required keys is empty. |
| `ModuleNotFoundError: anthropic` or similar | Re-run `backend/.venv/bin/pip install -r backend/requirements.txt`. |
| Voice button says "permission denied" | macOS mic permission: System Settings → Privacy & Security → Microphone → enable your browser. |
| Voice fails with `api_version_mismatch` | Make sure `OPENAI_REALTIME_MODEL` is either unset or `gpt-realtime` (NOT the beta preview ID). |
| Vite proxy returns 404 on `/api/*` | Confirm `frontend/vite.config.js` does NOT rewrite the `/api` prefix. |
| Supabase signup rejected | Turn off "Confirm email" in Supabase Auth settings, or use a real email. |

---

## 9. What's where

```
jarvis-recovered/
├── .env                          ← you create this (gitignored)
├── .gitignore
├── LOCKED_STATE.md               ← invariants + architecture notes
├── SETUP.md                      ← this file
├── README.md
├── scripts/
│   └── start-dev.sh              ← launcher used in step 6
├── backend/
│   ├── .env.example              ← template you copied in step 4
│   ├── .venv/                    ← created in step 5 (gitignored)
│   ├── requirements.txt
│   ├── sql/
│   │   ├── 000_base.sql          ← run first
│   │   ├── 001_subjects.sql      ← run second
│   │   └── 002_meal_buddy.sql    ← run third
│   └── src/
│       ├── main.py               ← FastAPI entrypoint
│       ├── auth.py               ← Supabase JWT verify dep
│       ├── supabase_client.py    ← service-role client singleton
│       ├── routes/               ← calendar_parser, voice, chat, admin,
│       │                           realtime, subjects, meal_buddy
│       └── services/             ← calendar_sync, realtime_voice,
│                                    material_extraction, storage
└── frontend/
    ├── .env.example              ← template you copied in step 4
    ├── .env.local                ← you create this (gitignored)
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── AppRouter.jsx         ← routes all 11 pages
        ├── AuthProvider.jsx
        ├── layouts/              ← AdminShell, JarvisShell
        ├── pages/                ← 11 pages incl. SubjectsList, MealBuddyHub, EventPage
        ├── components/           ← Calendar, MealBuddyNav, SubjectChat, ...
        ├── hooks/                ← useEvents, useJarvis, useRealtime, useVoice, useWakeWord
        └── lib/                  ← api.js, supabase.js
```

For the locked invariants (things that will break if you touch them), see `LOCKED_STATE.md`.
