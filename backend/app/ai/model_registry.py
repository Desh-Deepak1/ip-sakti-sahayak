MODEL_REGISTRY = {
    "fast_general": {
        "provider": "groq",
        "model": "llama-3.1-8b-instant",
        "max_output_tokens": 150
    },
    "rag_answer": {
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "max_output_tokens": 800
    },
    "complex_reasoning": {
        "provider": "gemini",
        "model": "gemini-3.7-flash",
        "max_output_tokens": 1500
    },
    "fallback": {
        "provider": "openrouter",
        "model": "google/gemma-4-31b-instruct",
        "max_output_tokens": 800
    }
}

def get_model_for_task(task_type: str) -> dict:
    return MODEL_REGISTRY.get(task_type, MODEL_REGISTRY["fallback"])