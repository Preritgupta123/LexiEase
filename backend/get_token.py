"""
Temporary script to get auth token for API testing.
DELETE after testing.
"""
from app.config import SUPABASE_URL, SUPABASE_ANON_KEY
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

response = supabase.auth.sign_in_with_password({
    "email": "preritgupta419@gmail.com",
    "password": "Prerit@419",
})

print("Access Token:")
print(response.session.access_token)