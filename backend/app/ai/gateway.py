import os
import httpx
from dotenv import load_dotenv

load_dotenv()

# Picking up the Groq API Key you set in .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async def process_llm_request(task_type: str, system_prompt: str, user_prompt: str, context: list) -> str:
    if not GROQ_API_KEY:
        return "Error: GROQ_API_KEY is missing."
    
    context_texts = []
    for chunk in context:
        payload = chunk.get("payload", {}) if isinstance(chunk, dict) else {}
        text = payload.get("text", "")
        if text: context_texts.append(text)
            
    combined_context = "\n\n".join(context_texts) if context_texts else "Rely on general IP and Ayurveda legal knowledge."
    full_user_prompt = f"Context Documents:\n{combined_context}\n\nUser Query:\n{user_prompt}"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Using Llama-3 or Qwen via Groq API for ultra-fast text generation
    payload = {
        "model": "qwen/qwen3.8-27b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_user_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1000
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions", 
                headers=headers, 
                json=payload, 
                timeout=45.0
            )
            
            if response.status_code != 200:
                return f"Groq API Error {response.status_code}: {response.text}"
                
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content
            
    except Exception as e:
        return f"Connection Failed: {str(e)}"