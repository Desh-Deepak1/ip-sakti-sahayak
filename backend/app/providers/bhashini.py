import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """
    MOCK BHASHINI ADAPTER:
    Approval pending. Currently returns the original text to prevent blocking MVP development.
    """
    if source_lang == target_lang:
        return text
        
    logger.info(f"Mock Translation Simulated: {source_lang} -> {target_lang}")
    
    # TODO: Replace with live ULCA pipeline inference endpoint once keys are approved.
    return text