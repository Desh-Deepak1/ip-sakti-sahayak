import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from supabase import create_client, Client

from app.api.deps import get_current_user
from app.rag.retriever import retrieve_evidence
from app.ai.gateway import process_llm_request

router = APIRouter(prefix="/api/v1", tags=["Chat"])

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"), 
    os.getenv("SUPABASE_SERVICE_KEY")
)

class ChatRequest(BaseModel):
    query: str
    jurisdiction: Optional[str] = "INDIA"
    product_category: Optional[str] = "PROPRIETARY_AYURVEDA"

@router.post("/chat")
async def chat_endpoint(request: ChatRequest, user_id: str = Depends(get_current_user)):
    try:
        user_query_lower = request.query.strip().lower()
        
        # 1. Quick General Query Intent Check (Saves API tokens)
        general_triggers = ["hi", "hello", "hey", "who are you", "how are you", "gm", "good morning", "sup", "thanks", "thank you"]
        is_general = user_query_lower in general_triggers or (len(user_query_lower.split()) <= 2 and not any(k in user_query_lower for k in ["act", "patent", "drug", "law", "ip", "ayurveda", "formulation", "trademark", "copyright", "design"]))

        if is_general:
            llm_text = (
                "Hello! I am IP-SAKTI Sahayak, your expert AI legal assistant for Intellectual Property and Ayurveda regulations. "
                "The question you asked is not related to legal or regulatory queries. Would you like to ask a legal query regarding IP, patents, or Ayurveda laws?"
            )
            citations = []
        else:
            # 2. Execute Context Retrieval for Legal Queries
            raw_chunks = await retrieve_evidence(request.query)
            
            system_prompt = (
                "You are IP-SAKTI Sahayak, an expert AI legal assistant for Ayurveda. "
                "Analyze the user's query strictly based on the provided Context Documents. "
                "Structure your EXACT response using THESE EXACT bolded headings:\n"
                "**Preliminary Assessment:**\n"
                "**Reasons:**\n"
                "**Relevant Statutory Provisions:**\n"
                "**Prior-Art Search Suggestions:**\n"
                "**ABS Warning:**\n"
                "**Next Action:**\n"
            )
            
            llm_text = await process_llm_request(
                task_type="rag_answer",
                system_prompt=system_prompt,
                user_prompt=request.query,
                context=raw_chunks
            )

            if "Error:" in llm_text:
                raise Exception(llm_text)

            # 3. Extract Dynamic Legal Citations from retrieved chunks
            citations = []
            for chunk in raw_chunks:
                payload = chunk.get("payload", {})
                if payload:
                    act_name = payload.get("act_name") or payload.get("title") or payload.get("document_name") or "Statutory Provision"
                    section = payload.get("section", "")
                    source_link = payload.get("source_link") or payload.get("url") or payload.get("link")
                    
                    if source_link:
                        citations.append({
                            "title": f"{act_name} {section}".strip(),
                            "type": "Statute / Document",
                            "url": source_link
                        })

            # Fallback if chunks don't have explicit links
            if not citations and not is_general:
                citations = [{
                    "title": "Indian Intellectual Property Portal",
                    "type": "Official Registry",
                    "url": "https://ipindia.gov.in"
                }]

            unique_citations = list({c["title"]: c for c in citations}.values())
            citations = unique_citations

        # 4. Upsert user profile & ALWAYS save chat history (both user query and response)
        try:
            user_info = supabase.auth.admin.get_user_by_id(user_id)
            user_email = user_info.user.email
        except Exception:
            user_email = f"user_{user_id[:8]}@ip-sakti.com"

        supabase.table("profiles").upsert({
            "id": user_id,
            "email": user_email
        }).execute()

        supabase.table("chat_sessions").insert({
            "user_id": user_id,
            "message_content": request.query,
            "role": "user"
        }).execute()

        supabase.table("chat_sessions").insert({
            "user_id": user_id,
            "message_content": llm_text,
            "role": "assistant"
        }).execute()

        return {
            "response": llm_text,
            "evidence_score": {"score": 1.0 if is_general else 0.95, "rating": "General" if is_general else "High Confidence"},
            "citations": citations,
            "disclaimer": "" if is_general else "IP-SAKTI Sahayak can make mistakes. Verify important information."
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Pipeline Execution Failed: {str(e)}")

@router.get("/history")
async def get_chat_history(user_id: str = Depends(get_current_user)):
    try:
        response = supabase.table("chat_sessions") \
            .select("message_content, role, created_at") \
            .eq("user_id", user_id) \
            .order("created_at", desc=False) \
            .execute()
        
        formatted_history = []
        for row in response.data:
            formatted_history.append({
                "sender": "assistant" if row["role"] == "assistant" else "user",
                "text": row["message_content"],
                "timestamp": row["created_at"]
            })
            
        return {"history": formatted_history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History Retrieval Failed: {str(e)}")

@router.delete("/history")
async def delete_chat_history(query: str, user_id: str = Depends(get_current_user)):
    try:
        supabase.table("chat_sessions").delete().eq("user_id", user_id).eq("message_content", query).execute()
        return {"status": "success", "message": "Chat deleted permanently from database"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))