import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

// Check if Supabase credentials are properly configured
const isSupabaseConfigured = supabaseUrl && 
  supabaseAnonKey && 
  supabaseUrl !== 'your_supabase_url_here' && 
  supabaseAnonKey !== 'your_supabase_anon_key_here'

// Create Supabase client only if properly configured
export const supabase = isSupabaseConfigured 
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null

export const isSupabaseEnabled = isSupabaseConfigured

// Mock auth for development when Supabase is not configured
export const mockAuth = {
  getSession: () => Promise.resolve({ data: { session: null } }),
  onAuthStateChange: () => ({ subscription: { unsubscribe: () => {} } }),
  signOut: () => Promise.resolve()
} 