from typing import List, Dict, Any

def validate_evidence(retrieved_chunks: List[Dict[str, Any]], score_threshold: float = 0.5) -> List[Dict[str, Any]]:
    valid_evidence = []
    for chunk in retrieved_chunks:
        score = chunk.get("score", 0.0)
        payload = chunk.get("payload", {})
        if score < score_threshold:
            continue
        if not payload.get("text"):
            continue
        if not payload.get("jurisdiction"):
            continue
        valid_evidence.append(chunk)
    return valid_evidence