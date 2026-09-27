import { createClient } from '@supabase/supabase-js';

// Vite environment variables ko import.meta.env se read karta hai
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// Ye line console me bata degi agar keys load nahi hui
if (!supabaseUrl || !supabaseAnonKey) {
    console.error("VITE_SUPABASE_URL ya VITE_SUPABASE_ANON_KEY missing hai .env file mein!");
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);