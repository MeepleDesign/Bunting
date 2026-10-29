import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import { SUPABASE_URL, SUPABASE_KEY } from './config';

// One browser client, shared by the demo runtime and the Next.js pages.
// The storage key is fixed so the login page and the demo see the same session.
export const STORAGE_KEY = 'bunting-auth';
let client: SupabaseClient | null = null;
export function supabase(): SupabaseClient {
  if (!client) client = createClient(SUPABASE_URL, SUPABASE_KEY, {
    auth: { persistSession: true, detectSessionInUrl: true, flowType: 'pkce', storageKey: STORAGE_KEY },
  });
  return client;
}
