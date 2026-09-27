import re

def clean_text(text: str) -> str:
    """Removes excessive whitespace and unprintable characters from extracted text."""
    if not text:
        return ""
    
    # Remove null characters and zero-width spaces
    text = text.replace('\x00', '').replace('\u200b', '')
    
    # Replace multiple whitespace characters (including newlines) with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    return text.strip()