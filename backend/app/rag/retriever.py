import os
from qdrant_client import AsyncQdrantClient
from fastembed import TextEmbedding
from dotenv import load_dotenv

load_dotenv()

# Match the model used during ingestion
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

qdrant = AsyncQdrantClient(
    url=os.getenv("QDRANT_URL"), 
    api_key=os.getenv("QDRANT_API_KEY")
)

async def retrieve_evidence(query: str, limit: int = 4) -> list:
    try:
        # Embed the user query locally instantly
        embeddings_generator = embedding_model.embed([query])
        query_vector = list(embeddings_generator)[0].tolist()

        # FIXED: Changed 'search' to 'query_points' and 'query_vector' to 'query'
        search_result = await qdrant.query_points(
            collection_name="ayurveda_ip_db_groq", 
            query=query_vector,
            limit=limit
        )
        
        # Safely extract points from the new query_points response structure
        hits = search_result.points if hasattr(search_result, 'points') else search_result
        return [{"payload": hit.payload} for hit in hits]
        
    except Exception as e:
        print(f"Retrieval Error: {str(e)}")
        return []