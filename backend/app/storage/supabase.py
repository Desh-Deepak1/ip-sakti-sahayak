import logging
from typing import Optional
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_supabase_client() -> Optional[Client]:
    if not settings.supabase_url or not settings.supabase_service_key:
        logger.warning("Supabase credentials not configured.")
        return None
    try:
        return create_client(settings.supabase_url, settings.supabase_service_key)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None