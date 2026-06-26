"""
Supabase client configuration (optional - only needed for cloud mode)
The app works with local SQLite by default.
"""
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

# Supabase client is only created when real credentials are provided
supabase = None
if SUPABASE_URL and SUPABASE_KEY and "your-" not in SUPABASE_URL:
    from supabase import create_client, Client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Using Supabase (cloud database)")
else:
    print("Using local SQLite database (no Supabase configured)")
