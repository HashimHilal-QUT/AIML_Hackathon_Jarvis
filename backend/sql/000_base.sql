-- ============================================================================
-- JARVIS base schema — run this FIRST in a fresh Supabase project.
--
-- Run order:
--   1. 000_base.sql      ← you are here  (profiles + events + signup trigger)
--   2. 001_subjects.sql                  (subjects + subject_materials)
--   3. 002_meal_buddy.sql                (dining_preferences + eateries + ...)
--
-- Everything uses `gen_random_uuid()` which is provided by the `pgcrypto`
-- extension. Supabase enables it by default, but we request it explicitly in
-- case you ever clone into a vanilla Postgres.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- profiles
--
-- One row per signed-in user, FK'd off auth.users. Every other user-scoped
-- table (events, subjects, dining_*, meal_matches) points at profiles(id),
-- so this MUST exist before any of the downstream migrations.
--
-- Columns in use:
--   id                      — same uuid as auth.users.id
--   name                    — display name (meal buddy list uses this)
--   character               — optional avatar/persona tag
--   qut_timetable_ics_url   — QUT aPlus timetable feed
--   qut_canvas_ics_url      — Canvas calendar feed
--   outlook_ics_url         — generic Outlook feed
--   google_ics_url          — generic Google feed
--   last_calendar_sync_at   — touched by calendar_sync.sync_user_feeds
-- ============================================================================
CREATE TABLE IF NOT EXISTS profiles (
  id                      uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  name                    text,
  character               text,
  qut_timetable_ics_url   text,
  qut_canvas_ics_url      text,
  outlook_ics_url         text,
  google_ics_url          text,
  last_calendar_sync_at   timestamptz,
  created_at              timestamptz NOT NULL DEFAULT now(),
  updated_at              timestamptz NOT NULL DEFAULT now()
);

-- Auto-create a profiles row every time a new auth.users row is inserted.
-- Without this, calendar_sync.ensure_profile_row() falls back to a lazy upsert,
-- but this trigger is cleaner for fresh signups.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  INSERT INTO public.profiles (id)
  VALUES (NEW.id)
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================================
-- events
--
-- Backing table for /event: calendar sync and manual events.
-- calendar_sync.py uses delete-then-insert per source, so we do NOT need the
-- (user_id, ics_uid) unique index that the original plan called out — but
-- it's still cheap and guards against double-inserts if sync logic changes.
-- ============================================================================
CREATE TABLE IF NOT EXISTS events (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  title        text NOT NULL,
  description  text,
  location     text,
  start_date   timestamptz NOT NULL,
  end_date     timestamptz,
  is_all_day   boolean NOT NULL DEFAULT false,
  event_type   text NOT NULL DEFAULT 'event',
  color        text DEFAULT '#534AB7',
  source       text NOT NULL DEFAULT 'manual',
  source_url   text,
  ics_uid      text,
  created_at   timestamptz NOT NULL DEFAULT now(),
  updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS events_user_start_idx
  ON events(user_id, start_date);
CREATE INDEX IF NOT EXISTS events_user_source_idx
  ON events(user_id, source);

-- Soft-unique: only enforced when ics_uid is non-null (manual events have NULL
-- and won't collide). Postgres allows multiple NULLs in a unique index by default.
CREATE UNIQUE INDEX IF NOT EXISTS events_user_ics_uid_key
  ON events(user_id, ics_uid)
  WHERE ics_uid IS NOT NULL;

-- ============================================================================
-- updated_at triggers
--
-- touch_updated_at() is also created by 001_subjects.sql with CREATE OR REPLACE,
-- so the order doesn't matter — whichever runs first wins, and the later one
-- is a no-op replace.
-- ============================================================================
CREATE OR REPLACE FUNCTION touch_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS profiles_touch_updated_at ON profiles;
CREATE TRIGGER profiles_touch_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

DROP TRIGGER IF EXISTS events_touch_updated_at ON events;
CREATE TRIGGER events_touch_updated_at
  BEFORE UPDATE ON events
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- ============================================================================
-- Storage bucket for subject materials (PDFs, images)
--
-- The backend auto-creates this via src/services/storage.py the first time a
-- material is uploaded, but creating it upfront keeps the setup predictable.
-- ============================================================================
INSERT INTO storage.buckets (id, name, public)
VALUES ('course-materials', 'course-materials', false)
ON CONFLICT (id) DO NOTHING;
