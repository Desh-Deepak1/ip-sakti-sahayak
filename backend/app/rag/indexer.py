import logging
from qdrant_client.http.models import VectorParams, Distance
from app.rag.qdrant import get_qdrant_client

logger = logging.getLogger(__name__)

def setup_qdrant_collection(collection_name: str = "legal_corpus") -> bool:
    client = get_qdrant_client()
    if not client:
        return False
        
    try:
        exists = client.collection_exists(collection_name=collection_name)
        if not exists:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
            )
            logger.info(f"Collection {collection_name} created successfully.")
        else:
            logger.info(f"Collection {collection_name} already exists.")
        return True
    except Exception as e:
        logger.error(f"Failed to setup collection: {e}")
        return False