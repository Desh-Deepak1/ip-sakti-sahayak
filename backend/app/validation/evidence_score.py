from typing import List, Dict, Any

def calculate_evidence_score(validated_claims: List[Dict[str, Any]], retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not validated_claims or not retrieved_chunks:
        return {"score": 0, "rating": "Insufficient Evidence", "abstain": True}
        
    total_claims = len(validated_claims)
    supported_claims = sum(1 for c in validated_claims if c["citation_valid"])
    citation_coverage = supported_claims / total_claims if total_claims > 0 else 0
    
    avg_relevance = sum(chunk.get("score", 0.0) for chunk in retrieved_chunks) / len(retrieved_chunks)
        
    final_score = (citation_coverage * 0.6) + (avg_relevance * 0.4)
    
    if final_score > 0.7:
        rating = "High Evidence"
        abstain = False
    elif final_score > 0.4:
        rating = "Medium Evidence"
        abstain = False
    elif final_score > 0.2:
        rating = "Low Evidence"
        abstain = False
    else:
        rating = "Insufficient Evidence"
        abstain = True
        
    return {
        "score": round(final_score, 2),
        "rating": rating,
        "abstain": abstain,
        "citation_coverage": round(citation_coverage, 2),
        "average_relevance": round(avg_relevance, 2)
    }