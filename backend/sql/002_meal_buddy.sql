-- Meal & Friends feature — one-time schema migration.
--
-- Run this ONCE in the Supabase Dashboard → SQL Editor:
--   https://supabase.com/dashboard/project/eredinmxmdlgeqfmgtsm/sql/new
--
-- Depends on:
--   * profiles (existing)
--   * touch_updated_at() function (already created by 001_subjects.sql)
--
-- Creates six tables powering the Meal & Friends feature:
--   1. dining_preferences   — user's cuisines / budget / dietary flags
--   2. eateries             — shared restaurant catalogue
--   3. dining_picks         — user's top picks for matching
--   4. dining_availability  — when the user is free to dine socially
--   5. meal_matches         — proposed / accepted / declined matches
--   6. dining_stats         — cached aggregate stats per user
--
-- Everything is scoped by user_id so the backend (using the service role
-- key with explicit filters) can safely read/write on behalf of one user
-- without leaking data across accounts.

-- ============================================================================
-- 1. dining_preferences
--
-- One row per student. Captures cuisine preferences, budget, and dietary
-- flags used by the matching algorithm.
--
-- We keep this separate from profiles.dietary (which already exists) so the
-- Meal & Friends feature can evolve independently. If you want the two
-- synced, add a trigger later.
-- ============================================================================
CREATE TABLE IF NOT EXISTS dining_preferences (
  user_id         uuid PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
  cuisines        text[] NOT NULL DEFAULT '{}',
  budget_amount   int NOT NULL DEFAULT 35 CHECK (budget_amount BETWEEN 5 AND 500),
  budget_tier     text NOT NULL DEFAULT '$$' CHECK (budget_tier IN ('$', '$$', '$$$')),
  dietary_flags   text[] NOT NULL DEFAULT '{}',
  custom_dietary  text[] NOT NULL DEFAULT '{}',
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

-- ============================================================================
-- 2. eateries
--
-- Shared catalogue of restaurants. NOT user-scoped — any signed-in user can
-- browse and pick any eatery. Seeded by the backend on first `GET /eateries`
-- with the 10 restaurants from the HTML mockups.
--
-- `is_trending` + `trending_rank` back the "HOT LIST" section on the Discover
-- page (rank 1-3 get the gold/cyan/green rank tags). `price_tier` is the
-- same $ / $$ / $$$ scheme used in dining_preferences for consistent filtering.
-- ============================================================================
CREATE TABLE IF NOT EXISTS eateries (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name           text NOT NULL,
  blurb          text,
  cuisine        text,
  price_low      int,
  price_high     int,
  price_tier     text CHECK (price_tier IN ('$', '$$', '$$$')),
  rating         numeric(3,1),
  location       text,
  image_url      text,
  tags           text[] NOT NULL DEFAULT '{}',
  is_trending    boolean NOT NULL DEFAULT false,
  trending_rank  int,
  created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS eateries_trending_idx
  ON eateries(is_trending, trending_rank);
CREATE INDEX IF NOT EXISTS eateries_cuisine_idx ON eateries(cuisine);

-- ============================================================================
-- 3. dining_picks
--
-- User's curated list of up to 3 eateries they want to use as matching
-- candidates. The UNIQUE constraint ensures you can't pick the same eatery
-- twice.
-- ============================================================================
CREATE TABLE IF NOT EXISTS dining_picks (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  eatery_id  uuid NOT NULL REFERENCES eateries(id) ON DELETE CASCADE,
  priority   int NOT NULL DEFAULT 1,
  added_at   timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, eatery_id)
);

CREATE INDEX IF NOT EXISTS dining_picks_user_idx ON dining_picks(user_id);

-- ============================================================================
-- 4. dining_availability
--
-- When the user is free to eat socially. One row = one slot on one day.
-- `slot_time` uses canonical 4-digit strings ('1130', '1230', '1800', '1900')
-- so both the UI grid and the matcher can join on exact string equality.
-- ============================================================================
CREATE TABLE IF NOT EXISTS dining_availability (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  slot_date   date NOT NULL,
  slot_time   text NOT NULL,
  meal_type   text NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner')),
  created_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, slot_date, slot_time)
);

CREATE INDEX IF NOT EXISTS dining_availability_user_date_idx
  ON dining_availability(user_id, slot_date);

-- ============================================================================
-- 5. meal_matches
--
-- One row per dining match proposal between two users at a specific eatery
-- and time. Match factors (cuisine align, schedule fit, etc.) are stored
-- inline as jsonb to avoid a separate factors table.
--
-- Status lifecycle:
--   proposed   — one user (or Jarvis) created the match; neither side has
--                confirmed yet
--   accepted   — both a_response='accepted' AND b_response='accepted'
--   declined   — at least one side responded 'declined'
--   completed  — past scheduled_at and was accepted
--   cancelled  — explicitly killed after being accepted
-- ============================================================================
CREATE TABLE IF NOT EXISTS meal_matches (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_a_id           uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  user_b_id           uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  eatery_id           uuid NOT NULL REFERENCES eateries(id) ON DELETE CASCADE,
  scheduled_at        timestamptz NOT NULL,
  meal_type           text NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner')),
  status              text NOT NULL DEFAULT 'proposed' CHECK (status IN (
                        'proposed', 'accepted', 'declined', 'completed', 'cancelled'
                      )),
  a_response          text CHECK (a_response IS NULL OR a_response IN ('accepted', 'declined')),
  b_response          text CHECK (b_response IS NULL OR b_response IN ('accepted', 'declined')),
  compatibility_score int NOT NULL DEFAULT 0 CHECK (compatibility_score BETWEEN 0 AND 100),
  match_factors       jsonb NOT NULL DEFAULT '{}'::jsonb,
  proposed_by         uuid REFERENCES profiles(id) ON DELETE SET NULL,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),
  CHECK (user_a_id <> user_b_id)
);

CREATE INDEX IF NOT EXISTS meal_matches_user_a_idx ON meal_matches(user_a_id);
CREATE INDEX IF NOT EXISTS meal_matches_user_b_idx ON meal_matches(user_b_id);
CREATE INDEX IF NOT EXISTS meal_matches_status_idx ON meal_matches(status);
CREATE INDEX IF NOT EXISTS meal_matches_scheduled_idx ON meal_matches(scheduled_at);

-- ============================================================================
-- 6. dining_stats
--
-- Cached per-user aggregates shown on the Discover page stats strip.
-- Updated by backend code on relevant events (match completed, eatery visited).
-- ============================================================================
CREATE TABLE IF NOT EXISTS dining_stats (
  user_id           uuid PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
  matches_made      int NOT NULL DEFAULT 0,
  points_earned     int NOT NULL DEFAULT 0,
  eateries_visited  int NOT NULL DEFAULT 0,
  social_rank_pct   int,
  updated_at        timestamptz NOT NULL DEFAULT now()
);

-- ============================================================================
-- updated_at triggers — reuse the touch_updated_at() function created by
-- 001_subjects.sql so we don't redefine it here.
-- ============================================================================
DROP TRIGGER IF EXISTS dining_preferences_touch ON dining_preferences;
CREATE TRIGGER dining_preferences_touch
  BEFORE UPDATE ON dining_preferences
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

DROP TRIGGER IF EXISTS meal_matches_touch ON meal_matches;
CREATE TRIGGER meal_matches_touch
  BEFORE UPDATE ON meal_matches
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

DROP TRIGGER IF EXISTS dining_stats_touch ON dining_stats;
CREATE TRIGGER dining_stats_touch
  BEFORE UPDATE ON dining_stats
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
