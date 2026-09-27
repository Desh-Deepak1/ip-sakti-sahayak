import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings

async def generate_openrouter_response(
    model: str, 
    system_prompt: str, 
    user_prompt: str, 
    context: Optional[List[Dict[str, Any]]] = None, 
    max_tokens: int = 800
) -> str:
    if not settings.openrouter_api_key:
        raise ValueError("OpenRouter API key missing")

    messages = [{"role": "system", "content": system_prompt}]
    
    if context:
        context_str = "\n".join([str(c) for c in context])
        messages.append({"role": "user", "content": f"Context:\n{context_str}"})
        
    messages.append({"role": "user", "content": user_prompt})

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "IP-SAKTI-Sahayak",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.1
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]