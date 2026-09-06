"""
Supabase client initialization
"""
from supabase import create_client, Client
from app.core.config import settings


def get_supabase_client() -> Client:
    """Get Supabase client with anon key (for read operations)"""
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY must be set in environment variables. "
            "See .env.example for configuration."
        )
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def get_supabase_admin_client() -> Client:
    """Get Supabase client with service role key (for write operations)"""
    key = settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_KEY
    if not settings.SUPABASE_URL or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables."
        )
    return create_client(settings.SUPABASE_URL, key)


# Singleton clients
_client: Client = None
_admin_client: Client = None


def get_db() -> Client:
    """Get or create the Supabase client singleton"""
    global _client
    if _client is None:
        _client = get_supabase_client()
    return _client


def get_admin_db() -> Client:
    """Get or create the Supabase admin client singleton"""
    global _admin_client
    if _admin_client is None:
        _admin_client = get_supabase_admin_client()
    return _admin_client
