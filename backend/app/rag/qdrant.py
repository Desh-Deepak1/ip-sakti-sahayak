import logging
from typing import Optional
from qdrant_client import QdrantClient
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_qdrant_client() -> Optional[QdrantClient]:
    if not settings.qdrant_url or not settings.qdrant_api_key:
        logger.warning("Qdrant credentials not configured.")
        return None
    try:
        return QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key
        )
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant client: {e}")
        return None