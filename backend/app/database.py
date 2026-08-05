
"""
Supabase client initialization.

This module creates a single, reusable Supabase client instance
that other parts of the app (routers, services) can import.
"""

from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

# We use the service_role key on the backend because our server
# is a trusted environment. Row-Level Security (RLS) policies
# (set up later) will still control what data users can access
# via the frontend using the anon key.
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)