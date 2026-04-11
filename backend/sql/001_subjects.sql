-- Subjects feature — one-time schema migration.
--
-- Run this once in the Supabase Dashboard → SQL Editor:
--   https://supabase.com/dashboard/project/eredinmxmdlgeqfmgtsm/sql/new
--
-- Creates:
--   * subjects            — one row per course the student is taking
--   * subject_materials   — unified material table (syllabus | module | rubric | assignment | file | note)
--
-- Foreign keys cascade from profiles → subjects → subject_materials so
-- deleting a user cleanly removes everything they owned. Matches the
-- pattern used by `events` / `reminders` / `assignments` in this project.

-- ---------------------------------------------------------------------------
-- subjects
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subjects (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  name        text NOT NULL,
  code        text,
  color       text DEFAULT '#00d4ff',
  description text,
  term        text,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS subjects_user_id_idx ON subjects(user_id);
CREATE INDEX IF NOT EXISTS subjects_user_code_idx ON subjects(user_id, code);

-- ---------------------------------------------------------------------------
-- subject_materials
--
-- One table for everything Jarvis might need as context about a course:
--   kind='syllabus'    — the course outline (usually one per subject)
--   kind='module'      — week/topic modules, lecture notes
--   kind='rubric'      — assignment marking rubrics
--   kind='assignment'  — assignment brief / instructions
--   kind='file'        — raw PDFs, slides, anything else
--   kind='note'        — student's own notes
--
-- content_text holds the searchable text (OCR'd from images, extracted
-- from PDFs, or pasted directly). file_path is the Supabase Storage path
-- for downloadable assets.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subject_materials (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_id   uuid NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  user_id      uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  kind         text NOT NULL CHECK (kind IN (
                 'syllabus', 'module', 'rubric', 'assignment', 'file', 'note'
               )),
  title        text,
  content_text text,
  file_path    text,
  file_name    text,
  file_type    text,
  file_size    int,
  metadata     jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at   timestamptz NOT NULL DEFAULT now(),
  updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS subject_materials_subject_id_idx
  ON subject_materials(subject_id);
CREATE INDEX IF NOT EXISTS subject_materials_user_id_idx
  ON subject_materials(user_id);
CREATE INDEX IF NOT EXISTS subject_materials_kind_idx
  ON subject_materials(subject_id, kind);

-- ---------------------------------------------------------------------------
-- Trigger to keep updated_at fresh on UPDATE
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION touch_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS subjects_touch_updated_at ON subjects;
CREATE TRIGGER subjects_touch_updated_at
  BEFORE UPDATE ON subjects
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

DROP TRIGGER IF EXISTS subject_materials_touch_updated_at ON subject_materials;
CREATE TRIGGER subject_materials_touch_updated_at
  BEFORE UPDATE ON subject_materials
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
