import { createClient } from '@supabase/supabase-js';
import type { Database } from '../types/supabase';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const isSupabaseConnected = () => {
  if (!supabaseUrl || !supabaseAnonKey) return false;
  try {
    new URL(supabaseUrl);
    return true;
  } catch (e) {
    return false;
  }
};

export const supabase = isSupabaseConnected()
  ? createClient<Database>(supabaseUrl, supabaseAnonKey)
  : null;