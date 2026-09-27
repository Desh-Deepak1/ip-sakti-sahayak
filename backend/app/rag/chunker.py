from typing import List, Dict, Any

def create_chunks(pages: List[Dict[str, Any]], metadata: Dict[str, Any], max_chars: int = 1500) -> List[Dict[str, Any]]:
    chunks = []
    chunk_id_counter = 1
    
    for page in pages:
        text = page["text"]
        paragraphs = text.split("\n\n")
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) > max_chars:
                chunks.append({
                    "chunk_id": f"{metadata.get('document_id', 'doc')}_{chunk_id_counter}",
                    "text": current_chunk.strip(),
                    "page": page["page_number"],
                    "embedding_model": "LFM2.5-Embedding-350M",
                    **metadata
                })
                chunk_id_counter += 1
                current_chunk = para
            else:
                current_chunk += " " + para
                
        if current_chunk.strip():
            chunks.append({
                "chunk_id": f"{metadata.get('document_id', 'doc')}_{chunk_id_counter}",
                "text": current_chunk.strip(),
                "page": page["page_number"],
                "embedding_model": "LFM2.5-Embedding-350M",
                **metadata
            })
            chunk_id_counter += 1
            
    return chunks