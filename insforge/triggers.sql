-- Optional: auto-create arena profile on auth signup.
-- InsForge auth.users uses `profile` jsonb (not raw_user_meta_data).
-- Client-side ensureProfile() is the primary path; this trigger is a backup.
-- To enable: npx @insforge/cli db import insforge/triggers.sql -y

CREATE OR REPLACE FUNCTION public.handle_new_arena_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, display_name, role)
  VALUES (
    NEW.id,
    COALESCE(NEW.profile->>'name', split_part(NEW.email, '@', 1)),
    'user'
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created_arena ON auth.users;
CREATE TRIGGER on_auth_user_created_arena
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_arena_user();
