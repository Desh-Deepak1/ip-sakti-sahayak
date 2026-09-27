import logging
import uuid
from typing import Dict, Any
from qdrant_client.http.models import PointStruct
from app.rag.parser import extract_text_from_pdf
from app.rag.chunker import create_chunks
from app.rag.embeddings import get_embeddings
from app.rag.qdrant import get_qdrant_client

logger = logging.getLogger(__name__)

async def process_and_ingest_pdf(file_path: str, metadata: Dict[str, Any]) -> bool:
    pages = extract_text_from_pdf(file_path)
    if not pages:
        return False
        
    chunks = create_chunks(pages, metadata)
    if not chunks:
        return False
        
    texts = [chunk["text"] for chunk in chunks]
    
    try:
        vectors = await get_embeddings(texts)
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return False
        
    client = get_qdrant_client()
    if not client:
        return False
        
    points = []
    for i, chunk in enumerate(chunks):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vectors[i],
                payload=chunk
            )
        )
        
    try:
        client.upsert(
            collection_name="legal_corpus",
            points=points
        )
        logger.info(f"Ingested {len(points)} chunks into Qdrant.")
        return True
    except Exception as e:
        logger.error(f"Qdrant upload failed: {e}")
        return False