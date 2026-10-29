-- Bunting hosted demo: a document store that matches the prototype's db API,
-- plus members (who can write) and display names.
-- Tables are prefixed bunting_ because they share a Supabase project with other apps.

create table if not exists public.bunting_members (
  email text primary key check (email = lower(email)),
  role text not null check (role in ('owner','contributor')),
  added_at timestamptz not null default now()
);

create table if not exists public.bunting_profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  name text not null default '' check (char_length(name) <= 80),
  updated_at timestamptz not null default now()
);

create table if not exists public.bunting_docs (
  path text primary key,
  coll text not null,
  doc_id text not null,
  data jsonb not null,
  updated_by uuid default auth.uid(),
  updated_at timestamptz not null default now(),
  constraint bunting_docs_path check (path = coll || '/' || doc_id),
  constraint bunting_docs_size check (octet_length(data::text) <= 262144)
);
create index if not exists bunting_docs_coll on public.bunting_docs (coll);

create or replace function public.bunting_role() returns text
language sql stable security definer set search_path = public as $$
  select role from public.bunting_members where email = lower(coalesce(auth.jwt()->>'email',''))
$$;
create or replace function public.bunting_is_member() returns boolean
language sql stable security definer set search_path = public as $$ select public.bunting_role() is not null $$;
create or replace function public.bunting_is_owner() returns boolean
language sql stable security definer set search_path = public as $$ select public.bunting_role() = 'owner' $$;

alter table public.bunting_members enable row level security;
alter table public.bunting_profiles enable row level security;
alter table public.bunting_docs enable row level security;

-- members: the owner manages the list; anyone signed in can see their own row
create policy "members: own row or owner" on public.bunting_members for select to authenticated
  using (email = lower(auth.jwt()->>'email') or public.bunting_is_owner());
create policy "members: owner adds" on public.bunting_members for insert to authenticated with check (public.bunting_is_owner());
create policy "members: owner edits" on public.bunting_members for update to authenticated using (public.bunting_is_owner()) with check (public.bunting_is_owner());
create policy "members: owner removes" on public.bunting_members for delete to authenticated using (public.bunting_is_owner() and email <> lower(auth.jwt()->>'email'));

-- profiles: names are visible to everyone (they appear in the demo); you edit your own
create policy "profiles: read" on public.bunting_profiles for select to anon, authenticated using (true);
create policy "profiles: insert own" on public.bunting_profiles for insert to authenticated with check (id = auth.uid());
create policy "profiles: update own" on public.bunting_profiles for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

-- docs: demo data is readable by anyone with the link; feedback is private to its author and the owner
create policy "docs: read" on public.bunting_docs for select to anon, authenticated
  using (coll <> 'feedback' or public.bunting_is_owner() or data->>'uid' = auth.uid()::text);
create policy "docs: insert" on public.bunting_docs for insert to authenticated with check (
  case coll
    when 'feedback' then data->>'uid' = auth.uid()::text or public.bunting_is_owner()
    when 'admin' then public.bunting_is_owner()
    else public.bunting_is_member() end);
create policy "docs: update" on public.bunting_docs for update to authenticated
  using (case coll
    when 'feedback' then data->>'uid' = auth.uid()::text or public.bunting_is_owner()
    when 'admin' then public.bunting_is_owner()
    else public.bunting_is_member() end)
  with check (case coll
    when 'feedback' then data->>'uid' = auth.uid()::text or public.bunting_is_owner()
    when 'admin' then public.bunting_is_owner()
    else public.bunting_is_member() end);
create policy "docs: delete" on public.bunting_docs for delete to authenticated
  using (case coll when 'feedback' then public.bunting_is_owner() when 'admin' then public.bunting_is_owner() else public.bunting_is_member() end);

-- live updates
alter table public.bunting_docs replica identity full;
alter publication supabase_realtime add table public.bunting_docs;

-- the owner
insert into public.bunting_members (email, role) values ('boardgames@meepledesign.com','owner') on conflict do nothing;
