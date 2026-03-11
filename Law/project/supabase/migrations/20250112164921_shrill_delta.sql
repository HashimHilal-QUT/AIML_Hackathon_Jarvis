/*
  # Add sample success stories

  1. Sample Data
    - Creates two lawyer accounts
    - Adds three success stories with different cases
    - Adds initial reactions and comments
*/

-- Create lawyer accounts in auth.users if they don't exist
INSERT INTO auth.users (id, email)
VALUES 
  ('550e8400-e29b-41d4-a716-446655440000', 'michael.chen@example.com'),
  ('6ba7b810-9dad-11d1-80b4-00c04fd430c8', 'emily.rodriguez@example.com')
ON CONFLICT (id) DO NOTHING;

-- Create user profiles if they don't exist
INSERT INTO users (id, email, role, full_name)
VALUES 
  ('550e8400-e29b-41d4-a716-446655440000', 'michael.chen@example.com', 'lawyer', 'Michael Chen'),
  ('6ba7b810-9dad-11d1-80b4-00c04fd430c8', 'emily.rodriguez@example.com', 'lawyer', 'Emily Rodriguez')
ON CONFLICT (id) DO NOTHING;

-- Create lawyer profiles if they don't exist
INSERT INTO lawyers (id, expertise, years_experience, bio, is_verified)
VALUES 
  ('550e8400-e29b-41d4-a716-446655440000', ARRAY['Corporate Law', 'Mergers & Acquisitions'], 12, 'Corporate law specialist with focus on M&A', true),
  ('6ba7b810-9dad-11d1-80b4-00c04fd430c8', ARRAY['Immigration Law', 'Human Rights'], 8, 'Dedicated immigration attorney', true)
ON CONFLICT (id) DO NOTHING;

-- Insert success stories
INSERT INTO stories (id, title, content, impact, lawyer_id, created_at)
VALUES
  (
    'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    'Successful Corporate Merger Worth $50M',
    'Led a complex merger between two mid-sized technology companies. The challenge involved navigating intricate regulatory requirements, addressing employee concerns, and ensuring smooth integration of company cultures. Through careful due diligence and strategic negotiation, we successfully completed the merger ahead of schedule.',
    'The merger resulted in preservation of all key jobs, 20% increase in market share, and creation of a stronger, more competitive entity in the tech sector. Employee satisfaction surveys showed 85% approval of the transition process.',
    '550e8400-e29b-41d4-a716-446655440000',
    NOW() - INTERVAL '3 days'
  ),
  (
    '550e8400-e29b-41d4-a716-446655440001',
    'Family Reunification After 5-Year Separation',
    'Represented a family separated due to complex immigration issues. The case involved multiple appeals, gathering extensive documentation, and coordinating with authorities across borders. We developed a comprehensive strategy that addressed both immediate and long-term immigration status concerns.',
    'Successfully reunited parents with their children after 5 years of separation. Secured permanent residency status for the entire family, allowing them to build a stable life together. The children are now excelling in school, and the parents have established successful careers in their field.',
    '6ba7b810-9dad-11d1-80b4-00c04fd430c8',
    NOW() - INTERVAL '5 days'
  ),
  (
    '550e8400-e29b-41d4-a716-446655440002',
    'Startup Protection Through Strategic IP Filing',
    'Helped a promising startup protect their revolutionary AI technology through strategic patent filings and comprehensive IP strategy. Coordinated with international patent offices and handled complex technical documentation.',
    'The startup successfully secured Series A funding of $10M, largely due to their protected IP portfolio. Their technology is now licensed to major tech companies, generating sustainable revenue streams.',
    '550e8400-e29b-41d4-a716-446655440000',
    NOW() - INTERVAL '7 days'
  )
ON CONFLICT (id) DO NOTHING;