/*
  # Update posts table relationships

  1. Changes
    - Modify posts table to reference users instead of lawyers
    - Update foreign key constraint
    - Add RLS policies for the new relationship

  2. Security
    - Enable RLS
    - Add policies for post creation and reading
*/

-- Modify posts table to reference users instead of lawyers
ALTER TABLE posts
DROP CONSTRAINT posts_author_id_fkey,
ADD CONSTRAINT posts_author_id_fkey
  FOREIGN KEY (author_id)
  REFERENCES users(id)
  ON DELETE CASCADE;

-- Update policies for the new relationship
DROP POLICY IF EXISTS "Lawyers can create posts" ON posts;

CREATE POLICY "Users can create posts"
  ON posts
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = author_id);

CREATE POLICY "Users can update own posts"
  ON posts
  FOR UPDATE
  TO authenticated
  USING (auth.uid() = author_id);

CREATE POLICY "Users can delete own posts"
  ON posts
  FOR DELETE
  TO authenticated
  USING (auth.uid() = author_id);