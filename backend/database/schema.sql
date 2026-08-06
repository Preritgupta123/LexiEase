-- ============================================
-- LexiEase Database Schema
-- This file documents the database structure.
-- Run this in Supabase SQL Editor to recreate
-- the database from scratch if needed.
-- ============================================


-- ============================================
-- STEP 1: Enable pgvector extension
-- ============================================
create extension if not exists vector;


-- ============================================
-- STEP 2: profiles table
-- ============================================
create table profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    full_name text,
    created_at timestamptz default now()
);

create function public.handle_new_user()
returns trigger as $$
begin
    insert into public.profiles (id, full_name)
    values (new.id, new.raw_user_meta_data->>'full_name');
    return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
    after insert on auth.users
    for each row execute procedure public.handle_new_user();


-- ============================================
-- STEP 3: documents table
-- ============================================
create table documents (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(id) on delete cascade not null,
    file_name text not null,
    file_path text not null,
    status text default 'uploaded' not null,
    created_at timestamptz default now()
);


-- ============================================
-- STEP 4: document_chunks table (RAG storage)
-- ============================================
create table document_chunks (
    id uuid primary key default gen_random_uuid(),
    document_id uuid references documents(id) on delete cascade not null,
    chunk_text text not null,
    chunk_index int not null,
    embedding vector(768),
    created_at timestamptz default now()
);

create index on document_chunks
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);


-- ============================================
-- STEP 5: analyses table
-- ============================================
create table analyses (
    id uuid primary key default gen_random_uuid(),
    document_id uuid references documents(id) on delete cascade not null,
    simplified_text text,
    risk_flags jsonb,
    created_at timestamptz default now()
);


-- ============================================
-- STEP 6: Enable Row Level Security
-- ============================================
alter table profiles enable row level security;
alter table documents enable row level security;
alter table document_chunks enable row level security;
alter table analyses enable row level security;


-- ============================================
-- STEP 7: RLS Policies - profiles
-- ============================================
create policy "Users can view own profile"
    on profiles for select
    using (auth.uid() = id);

create policy "Users can update own profile"
    on profiles for update
    using (auth.uid() = id);


-- ============================================
-- STEP 8: RLS Policies - documents
-- ============================================
create policy "Users can view own documents"
    on documents for select
    using (auth.uid() = user_id);

create policy "Users can insert own documents"
    on documents for insert
    with check (auth.uid() = user_id);

create policy "Users can delete own documents"
    on documents for delete
    using (auth.uid() = user_id);


-- ============================================
-- STEP 9: RLS Policies - document_chunks
-- ============================================
create policy "Users can view own document chunks"
    on document_chunks for select
    using (
        document_id in (
            select id from documents where user_id = auth.uid()
        )
    );


-- ============================================
-- STEP 10: RLS Policies - analyses
-- ============================================
create policy "Users can view own analyses"
    on analyses for select
    using (
        document_id in (
            select id from documents where user_id = auth.uid()
        )
    );