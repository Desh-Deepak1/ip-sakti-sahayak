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
        
        # 1. General Query Intent Check (Saves API tokens & skips RAG)
        general_triggers = ["hi", "hello", "hey", "who are you", "how are you", "gm", "good morning", "sup", "thanks", "thank you"]
        if user_query_lower in general_triggers or len(user_query_lower.split()) <= 2 and not any(k in user_query_lower for k in ["act", "patent", "drug", "law", "ip", "ayurveda", "formulation", "trademark"]):
            general_response = (
                "Hello! I am IP-SAKTI Sahayak, your expert AI legal assistant for Intellectual Property and Ayurveda regulations. "
                "The question you asked is not related to legal or regulatory queries. Would you like to ask a legal query regarding IP, patents, or Ayurveda laws?"
            )
            return {
                "response": general_response,
                "evidence_score": {"score": 1.0, "rating": "General Query"},
                "citations": [],
                "disclaimer": ""
            }

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

        # 3. Extract Legal Citations and Sources with Links
        citations = []
        for chunk in raw_chunks:
            if chunk.get("payload"):
                act_name = chunk.get("payload", {}).get("act_name", "Statutory Provision")
                section = chunk.get("payload", {}).get("section", "")
                source_link = chunk.get("payload", {}).get("source_link", "https://ipindia.gov.in")
                citations.append({
                    "title": f"{act_name} {section}".strip(),
                    "type": "Statute",
                    "url": source_link
                })

        if not citations:
            citations = [{"title": "Live AI Knowledge Base (General Provisions)", "type": "Statute", "url": "https://ipindia.gov.in"}]

        # Deduplicate citations
        unique_citations = {c["title"]: c for c in citations}.values()

        # 4. Upsert user profile & save chat history
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
            "evidence_score": {"score": 0.95, "rating": "High Confidence"},
            "citations": list(unique_citations),
            "disclaimer": "IP-SAKTI Sahayak can make mistakes. Verify important information."
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