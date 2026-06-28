-- Remove broken signup trigger (referenced non-existent raw_user_meta_data).
DROP TRIGGER IF EXISTS on_auth_user_created_arena ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_arena_user();
