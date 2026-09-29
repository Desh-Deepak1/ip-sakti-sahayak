import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from supabase import create_client, Client

from app.api.deps import get_current_user
from app.rag.retriever import retrieve_evidence
from app.ai.gateway import process_llm_request

# NEW: Bhashini translation function import karo
from app.providers.bhashini import translate_with_bhashini

router = APIRouter(prefix="/api/v1", tags=["Chat"])

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"), 
    os.getenv("SUPABASE_SERVICE_KEY")
)

class ChatRequest(BaseModel):
    query: str
    jurisdiction: Optional[str] = "INDIA"
    language: Optional[str] = "English"

@router.post("/chat")
async def chat_endpoint(request: ChatRequest, user_id: str = Depends(get_current_user)):
    try:
        user_query = request.query.strip()
        requested_language = request.language
        
        # AGENT 1: Intent & Classification Router
        intent_system_prompt = (
            "You are the Master Router Agent for IP-SAKTI Sahayak. Analyze the user's query and classify it into EXACTLY ONE of these categories:\n"
            "1. 'GENERAL': If it's a greeting, casual chat, asking how you work, or unrelated to IP/Ayurveda.\n"
            "2. 'NEEDS_CLASSIFICATION': If the user is asking about patenting or registering an Ayurvedic product, BUT has NOT explicitly stated if it is a 'Classical Medicine' (textbook based), 'Proprietary Formulation' (new mix), 'Cosmetic', or 'Extract/Phytopharmaceutical'.\n"
            "3. 'LEGAL_READY': If it is a clear legal/IP query and the product context is either clear or not required for the specific question.\n"
            "Reply with ONLY the category name. No extra words."
        )
        
        intent_check = await process_llm_request(
            task_type="rag_answer", 
            system_prompt=intent_system_prompt,
            user_prompt=user_query,
            context=[]
        )
        
        intent = intent_check.strip().upper()
        citations = []

        if "GENERAL" in intent:
            # Generate English response first
            general_system_prompt = (
                "You are IP-SAKTI Sahayak, an expert AI legal assistant for Intellectual Property and Ayurveda. "
                "Answer the casual greeting or general question politely and concisely in English. Remind them you are here for IP and Ayurveda legal queries."
            )
            llm_text = await process_llm_request(
                task_type="rag_answer",
                system_prompt=general_system_prompt,
                user_prompt=user_query,
                context=[]
            )
            score_data = {"score": 1.0, "rating": "General Chat"}
            disclaimer = ""

        elif "NEEDS_CLASSIFICATION" in intent:
            # Missing Category prompt in English
            llm_text = (
                "To give you the most accurate legal guidance, I need to understand your product better. "
                "Ayurvedic IP laws change based on the category. Could you please clarify if your product is:\n\n"
                "• **Classical Ayurvedic Medicine:** Formulated exactly as per ancient texts.\n"
                "• **Proprietary Ayurvedic Medicine:** A new combination of traditional herbs not mentioned in ancient texts.\n"
                "• **Phytopharmaceutical:** A highly purified, modern drug derived from plants requiring clinical trials.\n"
                "• **Cosmetic/Nutraceutical:** Meant for external application or dietary supplement.\n\n"
                "Please reply with your product category so I can fetch the correct regulations."
            )
            score_data = {"score": 1.0, "rating": "System Request"}
            disclaimer = ""

        else:
            # Full RAG in English (Because LLM performs best in English for legal texts)
            raw_chunks = await retrieve_evidence(user_query)
            
            system_prompt = (
                f"You are IP-SAKTI Sahayak, an expert AI legal assistant analyzing IP laws for the {request.jurisdiction} jurisdiction. "
                "Analyze the user's query strictly based on the provided Context Documents in English. "
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
                user_prompt=user_query,
                context=raw_chunks
            )

            if "Error:" in llm_text:
                raise Exception(llm_text)

            for chunk in raw_chunks:
                payload = chunk.get("payload", {})
                if payload:
                    act_name = payload.get("act_name") or payload.get("document_name") or "Statutory Provision"
                    section = payload.get("section", "")
                    source_link = payload.get("source_link") or payload.get("url") or "https://ipindia.gov.in"
                    citations.append({"title": f"{act_name} {section}".strip(), "type": "Statute / Official Document", "url": source_link})

            if not citations:
                citations = [{"title": "Indian Intellectual Property Portal", "type": "Official Registry", "url": "https://ipindia.gov.in"}]

            citations = list({c["title"]: c for c in citations}.values())
            score_data = {"score": 0.95, "rating": "High Confidence"}
            disclaimer = "IP-SAKTI Sahayak provides legal information based on trained datasets, not professional legal advice."

        # ==========================================
        # BHASHINI TRANSLATION LAYER (Runs for ALL intents)
        # ==========================================
        if requested_language.upper() == "HINDI":
            llm_text = await translate_with_bhashini(llm_text, source_lang="en", target_lang="hi")
            if disclaimer:
                disclaimer = await translate_with_bhashini(disclaimer, source_lang="en", target_lang="hi")
        elif requested_language.upper() == "MARATHI":
            llm_text = await translate_with_bhashini(llm_text, source_lang="en", target_lang="mr")
            if disclaimer:
                disclaimer = await translate_with_bhashini(disclaimer, source_lang="en", target_lang="mr")

        # Database Logging
        try:
            user_info = supabase.auth.admin.get_user_by_id(user_id)
            user_email = user_info.user.email
        except Exception:
            user_email = f"user_{user_id[:8]}@ip-sakti.com"

        supabase.table("profiles").upsert({"id": user_id, "email": user_email}).execute()
        supabase.table("chat_sessions").insert({"user_id": user_id, "message_content": user_query, "role": "user"}).execute()
        supabase.table("chat_sessions").insert({"user_id": user_id, "message_content": llm_text, "role": "assistant"}).execute()

        return {
            "response": llm_text,
            "evidence_score": score_data,
            "citations": citations,
            "disclaimer": disclaimer
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Pipeline Execution Failed: {str(e)}")

@router.get("/history")
async def get_chat_history(user_id: str = Depends(get_current_user)):
    try:
        response = supabase.table("chat_sessions").select("message_content, role, created_at").eq("user_id", user_id).order("created_at", desc=False).execute()
        return {"history": [{"sender": "assistant" if row["role"] == "assistant" else "user", "text": row["message_content"], "timestamp": row["created_at"]} for row in response.data]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History Retrieval Failed: {str(e)}")

@router.delete("/history")
async def delete_chat_history(query: str, user_id: str = Depends(get_current_user)):
    try:
        supabase.table("chat_sessions").delete().eq("user_id", user_id).eq("message_content", query).execute()
        return {"status": "success", "message": "Chat deleted permanently"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))