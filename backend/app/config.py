"""
Configuration module for LexiEase backend.

Loads environment variables and provides a single source of truth
for app-wide settings. Using a dedicated config module (instead of
scattering os.getenv() calls everywhere) makes it easy to see all
required settings at a glance and catch missing values early.
"""
import os
from dotenv import load_dotenv
# Load variables from .env file into environment
load_dotenv()
# Supabase settings
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
# SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
# Fail fast if critical config is missing (better than a confusing
# error deep inside the app later)
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError(
        "Missing Supabase configuration. "
        "Please check your backend/.env file."
    )