from typing import List

def route_ip(product_category: str, claims_novelty: bool = False) -> List[str]:
    domains = ["TRADEMARK", "COPYRIGHT"]
    
    if product_category == "PROPRIETARY_AYURVEDA" and claims_novelty:
        domains.extend(["PATENT", "TRADE_SECRET"])
    elif product_category == "PHYTOPHARMACEUTICAL":
        domains.append("PATENT")
    elif product_category == "CLASSICAL_AYURVEDA":
        domains.append("GI")
        
    return domains