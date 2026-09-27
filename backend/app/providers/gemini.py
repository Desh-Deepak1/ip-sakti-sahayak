import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings

async def generate_gemini_response(
    model: str, 
    system_prompt: str, 
    user_prompt: str, 
    context: Optional[List[Dict[str, Any]]] = None, 
    max_tokens: int = 1500
) -> str:
    if not settings.gemini_api_key:
        raise ValueError("Gemini API key missing")

    combined_prompt = f"System:\n{system_prompt}\n\n"
    if context:
        context_str = "\n".join([str(c) for c in context])
        combined_prompt += f"Context:\n{context_str}\n\n"
    combined_prompt += f"User:\n{user_prompt}"

    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [{"parts": [{"text": combined_prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.1
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.gemini_api_key}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]