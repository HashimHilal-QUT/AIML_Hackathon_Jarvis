/*
  # Add Stories Feature

  1. New Tables
    - `stories` table for lawyer success stories
      - `id` (uuid, primary key)
      - `title` (text)
      - `content` (text)
      - `impact` (text)
      - `lawyer_id` (uuid, references lawyers)
      - `created_at` (timestamptz)
      - `updated_at` (timestamptz)
    - `story_reactions` table for likes/loves
      - `id` (uuid, primary key)
      - `story_id` (uuid, references stories)
      - `user_id` (uuid, references users)
      - `type` (text, either 'like' or 'love')
    - `story_comments` table for comments
      - `id` (uuid, primary key)
      - `story_id` (uuid, references stories)
      - `user_id` (uuid, references users)
      - `content` (text)
      - `created_at` (timestamptz)

  2. Security
    - Enable RLS on all tables
    - Add appropriate policies for reading and writing
*/

-- Stories table
CREATE TABLE stories (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  content text NOT NULL,
  impact text NOT NULL,
  lawyer_id uuid REFERENCES lawyers(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE stories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read stories"
  ON stories
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Lawyers can create stories"
  ON stories
  FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM lawyers WHERE id = auth.uid()
    )
  );

CREATE POLICY "Lawyers can update own stories"
  ON stories
  FOR UPDATE
  TO authenticated
  USING (lawyer_id = auth.uid());

-- Story reactions table
CREATE TABLE story_reactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  story_id uuid REFERENCES stories(id) ON DELETE CASCADE,
  user_id uuid REFERENCES users(id) ON DELETE CASCADE,
  type text NOT NULL CHECK (type IN ('like', 'love')),
  created_at timestamptz DEFAULT now(),
  UNIQUE(story_id, user_id)
);

ALTER TABLE story_reactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read reactions"
  ON story_reactions
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can create reactions"
  ON story_reactions
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own reactions"
  ON story_reactions
  FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Story comments table
CREATE TABLE story_comments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  story_id uuid REFERENCES stories(id) ON DELETE CASCADE,
  user_id uuid REFERENCES users(id) ON DELETE CASCADE,
  content text NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE story_comments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read comments"
  ON story_comments
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can create comments"
  ON story_comments
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own comments"
  ON story_comments
  FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own comments"
  ON story_comments
  FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);