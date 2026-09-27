from typing import Dict
from app.decision.rules import REGULATORY_CATEGORIES

def classify_product(answers: Dict[str, bool]) -> str:
    """
    Deterministically classifies the product based on structured user answers.
    """
    if answers.get("is_food_or_nutrition") and not answers.get("makes_medicinal_claim"):
        return "AYURVEDA_AAHARA"
        
    if answers.get("is_cosmetic"):
        return "COSMETIC"
        
    if answers.get("in_classical_text") and not answers.get("has_new_ingredients"):
        return "CLASSICAL_AYURVEDA"
        
    if answers.get("is_purified_extract") and answers.get("makes_medicinal_claim"):
        return "PHYTOPHARMACEUTICAL"
        
    if answers.get("makes_medicinal_claim") and answers.get("has_new_ingredients"):
        return "PROPRIETARY_AYURVEDA"
        
    return "AMBIGUOUS_REQUIRES_EXPERT"