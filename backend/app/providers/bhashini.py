import os
import httpx

async def translate_with_bhashini(text: str, source_lang: str = "en", target_lang: str = "hi"):
    """
    Translates text using India's official Bhashini API (Dhruva).
    Language codes: 'hi' (Hindi), 'mr' (Marathi), 'en' (English) etc.
    """
    if source_lang == target_lang:
        return text

    api_key = os.getenv("BHASHINI_API_KEY")
    user_id = os.getenv("BHASHINI_USER_ID")
    bhashini_url = os.getenv("BHASHINI_URL", "https://dhruva-api.bhashini.gov.in/services/inference/pipeline")

    if not api_key:
        print("Warning: Bhashini API key not found. Returning original text.")
        return text

    # Bhashini Payload Structure (NMT - Neural Machine Translation)
    payload = {
        "pipelineTasks": [
            {
                "taskType": "translation",
                "config": {
                    "language": {
                        "sourceLanguage": source_lang,
                        "targetLanguage": target_lang
                    }
                }
            }
        ],
        "inputData": {
            "input": [
                {"source": text}
            ]
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": api_key,
        "userID": user_id
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(bhashini_url, json=payload, headers=headers, timeout=15.0)
            response.raise_for_status()
            data = response.json()
            
            # Extracting the translated text from Bhashini's response
            translated_text = data["pipelineResponse"][0]["output"][0]["target"]
            return translated_text
            
    except Exception as e:
        print(f"Bhashini Translation Error: {e}")
        return text  # Agar error aaye toh original English text return kar do taaki app crash na ho