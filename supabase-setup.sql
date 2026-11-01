-- Run this entire script in Supabase Dashboard > SQL Editor.
create extension if not exists pgcrypto;

create table if not exists public.couples (
  id uuid primary key default gen_random_uuid(),
  invite_code text unique not null default upper(substr(encode(gen_random_bytes(8),'hex'),1,8)),
  created_at timestamptz not null default now()
);
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  couple_id uuid not null references public.couples(id) on delete cascade,
  display_name text,
  created_at timestamptz not null default now()
);
-- Invite code is kept on couples; profiles only stores membership.
create table if not exists public.attendance (
  id uuid primary key default gen_random_uuid(),
  couple_id uuid not null references public.couples(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  day date not null,
  available boolean not null,
  updated_at timestamptz not null default now(),
  unique(user_id,day)
);

alter table public.couples enable row level security;
alter table public.profiles enable row level security;
alter table public.attendance enable row level security;

create or replace function public.is_couple_member(cid uuid)
returns boolean language sql stable security definer set search_path=public
as $$ select exists(select 1 from public.profiles where id=auth.uid() and couple_id=cid); $$;

create policy "members read own couple" on public.couples for select
using (exists(select 1 from public.profiles p where p.id=auth.uid() and p.couple_id=id));
create policy "profiles in same couple visible" on public.profiles for select
using (public.is_couple_member(couple_id));
create policy "attendance shared with couple" on public.attendance for select
using (public.is_couple_member(couple_id));
create policy "user writes own attendance" on public.attendance for insert
with check (user_id=auth.uid() and public.is_couple_member(couple_id));
create policy "user updates own attendance" on public.attendance for update
using (user_id=auth.uid() and public.is_couple_member(couple_id))
with check (user_id=auth.uid() and public.is_couple_member(couple_id));

-- First account creates a private couple space and receives its invite code.
create or replace function public.create_couple()
returns public.profiles language plpgsql security definer set search_path=public
as $$
declare c public.couples; p public.profiles;
begin
 if auth.uid() is null then raise exception 'Please log in first'; end if;
 if exists(select 1 from public.profiles where id=auth.uid()) then
   select * into p from public.profiles where id=auth.uid(); return p;
 end if;
 insert into public.couples default values returning * into c;
 insert into public.profiles(id,couple_id) values(auth.uid(),c.id) returning * into p;
 return p;
end $$;

-- Second account joins with the invite code. Maximum two members per couple.
create or replace function public.join_couple(invite text)
returns public.profiles language plpgsql security definer set search_path=public
as $$
declare c public.couples; p public.profiles; n integer;
begin
 if auth.uid() is null then raise exception 'Please log in first'; end if;
 if exists(select 1 from public.profiles where id=auth.uid()) then
   select * into p from public.profiles where id=auth.uid(); return p;
 end if;
 select * into c from public.couples where invite_code=upper(trim(invite));
 if c.id is null then raise exception 'That couple code was not found'; end if;
 select count(*) into n from public.profiles where couple_id=c.id;
 if n>=2 then raise exception 'This couple space already has two members'; end if;
 insert into public.profiles(id,couple_id) values(auth.uid(),c.id) returning * into p;
 return p;
end $$;

grant execute on function public.create_couple() to authenticated;
grant execute on function public.join_couple(text) to authenticated;
grant execute on function public.is_couple_member(uuid) to authenticated;
