import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from supabase import create_client, Client

from app.api.deps import get_current_user
from app.rag.retriever import retrieve_evidence
from app.ai.gateway import process_llm_request

router = APIRouter(prefix="/api/v1", tags=["Chat"])

# Initialize Supabase Client for Database Operations
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
        # 1. Execute Context Retrieval
        raw_chunks = await retrieve_evidence(request.query)
        
        # 2. Formulate System Prompt
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
        
        # 3. Generate Live LLM Response via Groq
        llm_text = await process_llm_request(
            task_type="rag_answer",
            system_prompt=system_prompt,
            user_prompt=request.query,
            context=raw_chunks
        )

        if "Error:" in llm_text:
            raise Exception(llm_text)

        # 4. Extract Legal Citations
        citations = list({
            chunk.get("payload", {}).get("act_name", "General Provisions") 
            for chunk in raw_chunks if chunk.get("payload")
        }) or ["Live AI Knowledge Base (General Provisions)"]

        # 5. NEW FIX: Fetch user email to satisfy the NOT NULL constraint in profiles table
        try:
            user_info = supabase.auth.admin.get_user_by_id(user_id)
            user_email = user_info.user.email
        except Exception:
            # Fallback just in case admin fetch fails, so the app never crashes
            user_email = f"user_{user_id[:8]}@ip-sakti.com"

        supabase.table("profiles").upsert({
            "id": user_id,
            "email": user_email
        }).execute()

        # 6. Persist Chat History to Supabase
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
            "evidence_score": {"score": 0.95, "rating": "Live AI Generated"},
            "citations": citations,
            "disclaimer": "IP-SAKTI Sahayak can make mistakes. Verify important information."
        }

    except Exception as e:
        import traceback
        print("\n" + "="*60)
        print("🚨 ASLI ERROR YAHAN HAI (BHEJO MUJHE):")
        traceback.print_exc()
        print("="*60 + "\n")
        raise HTTPException(status_code=500, detail=f"Pipeline Execution Failed: {str(e)}")

@router.get("/history")
async def get_chat_history(user_id: str = Depends(get_current_user)):
    try:
        # Retrieve chronological chat records for the authenticated user
        response = supabase.table("chat_sessions") \
            .select("message_content, role, created_at") \
            .eq("user_id", user_id) \
            .order("created_at", desc=False) \
            .execute()
        
        # Format the database rows into the structure expected by the React frontend
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