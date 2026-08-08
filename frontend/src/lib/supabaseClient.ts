/**
 * Supabase client for frontend use.
 *
 * Uses the anon key (safe for browser exposure) combined with
 * Row-Level Security policies (already configured in our database)
 * to ensure users can only access their own data.
 */

import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

// Fail fast during development if env vars are missing
if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Missing Supabase environment variables. Check frontend/.env file.'
  )
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

