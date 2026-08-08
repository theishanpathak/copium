import { createClient } from "@supabase/supabase-js";

// Server-only. The secret key bypasses RLS, so this must never be imported
// into a client component.
export const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SECRET_KEY!,
);