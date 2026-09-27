from typing import List, Dict, Any

def build_evidence_context(valid_chunks: List[Dict[str, Any]]) -> str:
    if not valid_chunks:
        return "NO_EVIDENCE_AVAILABLE"
        
    context_parts = []
    for chunk in valid_chunks:
        payload = chunk.get("payload", {})
        chunk_id = payload.get("chunk_id", "UNKNOWN_ID")
        act_name = payload.get("act_name", "UNKNOWN_ACT")
        jurisdiction = payload.get("jurisdiction", "UNKNOWN_JURISDICTION")
        text = payload.get("text", "")
        
        formatted_chunk = f"[EVIDENCE_ID: {chunk_id} | JURISDICTION: {jurisdiction} | SOURCE: {act_name}]\n{text}"
        context_parts.append(formatted_chunk)
        
    return "\n\n".join(context_parts)