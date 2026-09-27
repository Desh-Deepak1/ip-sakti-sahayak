import os
import uuid
from dotenv import load_dotenv
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

print("Loading local AI embedding model (No API keys needed!)...")
# BAAI/bge-small-en-v1.5 is a highly accurate, fast local embedding model (size: 384)
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL"), 
    api_key=os.getenv("QDRANT_API_KEY")
)

# Naya collection for Groq pipeline
COLLECTION_NAME = "ayurveda_ip_db_groq"

def setup_qdrant_collection():
    collections = qdrant.get_collections().collections
    if not any(col.name == COLLECTION_NAME for col in collections):
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        print(f"Collection '{COLLECTION_NAME}' ready.")

def chunk_text(text: str, chunk_size: int = 1000) -> list:
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - 100)]

def ingest_documents(directory_path: str):
    setup_qdrant_collection()
    
    for filename in os.listdir(directory_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory_path, filename)
            
            with open(file_path, "r", encoding="utf-8") as file:
                raw_text = file.read()
                
            chunks = chunk_text(raw_text)
            print(f"Processing {filename}: {len(chunks)} chunks (Bypassing API Limits)...")
            
            # Generate embeddings locally on your machine
            embeddings_generator = embedding_model.embed(chunks)
            embeddings_list = list(embeddings_generator)
            
            points = []
            for i, vector in enumerate(embeddings_list):
                points.append(
                    PointStruct(
                        id=str(uuid.uuid4()), 
                        vector=vector.tolist(), 
                        payload={"text": chunks[i], "source": filename, "act_name": "Indian Legal Framework"}
                    )
                )
            
            # Batch upload to Qdrant
            qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
            print(f"Successfully uploaded {filename} without any API Limits!\n")

if __name__ == "__main__":
    data_directory = os.path.join(BASE_DIR, "data")
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)
        print(f"Created directory {data_directory}. Add .txt files and rerun.")
    else:
        ingest_documents(data_directory)