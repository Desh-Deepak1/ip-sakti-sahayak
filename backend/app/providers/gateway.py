import logging
from typing import Dict, Any, List, Optional
from app.ai.model_registry import get_model_for_task
from app.providers.groq import generate_groq_response
from app.providers.gemini import generate_gemini_response
from app.providers.openrouter import generate_openrouter_response

logger = logging.getLogger(__name__)

async def process_llm_request(
    task_type: str, 
    system_prompt: str, 
    user_prompt: str, 
    context: Optional[List[Dict[str, Any]]] = None
) -> str:
    model_config = get_model_for_task(task_type)
    provider = model_config["provider"]
    model_id = model_config["model"]
    max_tokens = model_config.get("max_output_tokens", 500)
    
    try:
        if provider == "groq":
            return await generate_groq_response(model_id, system_prompt, user_prompt, context, max_tokens)
        elif provider == "gemini":
            return await generate_gemini_response(model_id, system_prompt, user_prompt, context, max_tokens)
        elif provider == "openrouter":
            return await generate_openrouter_response(model_id, system_prompt, user_prompt, context, max_tokens)
        else:
            logger.error(f"Unknown provider: {provider}")
            return "System abstains due to unrecognized provider configuration."
    except Exception as e:
        logger.error(f"Provider {provider} failed on task {task_type}: {e}")
        raise e