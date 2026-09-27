from typing import List, Dict, Any
from app.schemas.response import Claim

def validate_citations(llm_claims: List[Claim], retrieved_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    valid_chunk_ids = {chunk.get("payload", {}).get("chunk_id") for chunk in retrieved_chunks if chunk.get("payload")}
    
    validated_claims = []
    for claim in llm_claims:
        valid_evidence = [eid for eid in claim.evidence_ids if eid in valid_chunk_ids]
        
        if valid_evidence:
            validated_claims.append({
                "claim_text": claim.claim_text,
                "evidence_ids": valid_evidence,
                "citation_valid": True
            })
        else:
            validated_claims.append({
                "claim_text": claim.claim_text,
                "evidence_ids": [],
                "citation_valid": False
            })
            
    return validated_claims