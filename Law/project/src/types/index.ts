export type UserRole = 'user' | 'lawyer' | 'admin';

export interface User {
  id: string;
  email: string;
  role: UserRole;
  full_name: string;
  created_at: string;
}

export interface Lawyer extends User {
  expertise: string[];
  years_experience: number;
  bio: string;
  consultation_fee: number;
  rating: number;
  certifications: string[];
  is_verified: boolean;
  location: string;
}

export interface Post {
  id: string;
  title: string;
  content: string;
  author_id: string;
  created_at: string;
  likes_count: number;
  comments_count: number;
  category: string;
}

export interface Consultation {
  id: string;
  user_id: string;
  lawyer_id: string;
  status: 'pending' | 'accepted' | 'declined' | 'completed';
  scheduled_for: string;
  created_at: string;
  notes: string;
}