from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    environment: str = "development"
    
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    bhashini_api_key: Optional[str] = None
    
    qdrant_url: Optional[str] = None
    qdrant_api_key: Optional[str] = None
    
    supabase_url: Optional[str] = None
    supabase_service_key: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()