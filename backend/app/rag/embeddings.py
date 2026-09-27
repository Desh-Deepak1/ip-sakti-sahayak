import httpx
from typing import List
from app.core.config import settings

async def get_embeddings(texts: List[str], model: str = "liquid/lfm-2.5-embedding-350m") -> List[List[float]]:
    if not settings.openrouter_api_key:
        raise ValueError("OpenRouter API key missing")
        
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "IP-SAKTI-Sahayak"
    }
    
    payload = {
        "model": model,
        "input": texts
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/embeddings",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]