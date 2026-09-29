import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from supabase import create_client, Client

from app.api.deps import get_current_user
from app.rag.retriever import retrieve_evidence
from app.ai.gateway import process_llm_request

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
        jurisdiction_selection = request.jurisdiction.upper()
        
        # AGENT 1: Intent & Classification Router
        intent_system_prompt = (
            "You are the Master Router Agent for IP-SAKTI Sahayak. Classify the user's query into EXACTLY ONE category:\n"
            "1. 'GENERAL': Greeting, casual chat, or unrelated to IP/Ayurveda.\n"
            "2. 'NEEDS_CLASSIFICATION': Asking about patenting an Ayurvedic product but hasn't stated if it is 'Classical', 'Proprietary', 'Phytopharmaceutical', or 'Cosmetic'.\n"
            "3. 'LEGAL_READY': Clear legal/IP query.\n"
            "Reply with ONLY the category name."
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
            general_system_prompt = "You are IP-SAKTI Sahayak. Answer the casual greeting politely in English in 1 sentence. Remind them to ask IP/Ayurveda legal queries."
            llm_text = await process_llm_request(task_type="rag_answer", system_prompt=general_system_prompt, user_prompt=user_query, context=[])
            score_data = {"score": 1.0, "rating": "General Chat"}
            disclaimer = ""

        elif "NEEDS_CLASSIFICATION" in intent:
            llm_text = (
                "To give you the most accurate legal guidance, I need to understand your product better. "
                "Ayurvedic IP laws change based on the category. Could you please clarify if your product is:\n\n"
                "• **Classical Ayurvedic Medicine:** Formulated exactly as per ancient texts.\n"
                "• **Proprietary Ayurvedic Medicine:** A new combination of traditional herbs not mentioned in ancient texts.\n"
                "• **Phytopharmaceutical:** A highly purified, modern drug derived from plants requiring clinical trials.\n"
                "• **Cosmetic/Nutraceutical:** Meant for external application or dietary supplement.\n\n"
                "Please reply with your product category."
            )
            score_data = {"score": 1.0, "rating": "System Request"}
            disclaimer = ""

        else:
            raw_chunks = await retrieve_evidence(user_query)
            
            if jurisdiction_selection == "INTERNATIONAL":
                jurisdiction_rules = (
                    "CRITICAL GUARDRAIL: The user selected INTERNATIONAL jurisdiction. "
                    "You MUST base your analysis ONLY on International Treaties (e.g., TRIPS Agreement, WIPO Treaties, CBD, Nagoya Protocol, PCT). "
                    "DO NOT enforce Indian national laws (like Indian Patents Act 1970 or Biological Diversity Act 2002) as binding internationally. Explain international patentability and global ABS frameworks."
                )
            else:
                jurisdiction_rules = (
                    "CRITICAL GUARDRAIL: The user selected INDIA jurisdiction. "
                    "You MUST strictly apply Indian National Laws, specifically the Patents Act 1970 (emphasizing Section 3(p)), "
                    "the Biological Diversity Act 2002 (ABS compliance and NBA approval), and the Drugs and Cosmetics Act 1940. Reference TKDL."
                )

            system_prompt = (
                f"You are IP-SAKTI Sahayak, an expert AI legal assistant. {jurisdiction_rules}\n"
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

            if "Error:" in llm_text: raise Exception(llm_text)

            for chunk in raw_chunks:
                payload = chunk.get("payload", {})
                if payload:
                    act_name = payload.get("act_name") or payload.get("document_name") or "Statutory Provision"
                    section = payload.get("section", "")
                    source_link = payload.get("source_link") or payload.get("url") or "https://ipindia.gov.in"
                    citations.append({"title": f"{act_name} {section}".strip(), "type": "Statute / Official Document", "url": source_link})

            if not citations:
                citations = [{"title": "Intellectual Property Portal", "type": "Official Registry", "url": "https://ipindia.gov.in"}]

            citations = list({c["title"]: c for c in citations}.values())
            score_data = {"score": 0.95, "rating": "High Confidence"}
            disclaimer = "IP-SAKTI Sahayak provides legal information based on trained datasets, not professional legal advice."

        # --- MULTILINGUAL TRANSLATION (All 22 Indian Scheduled Languages) ---
        bhashini_lang_codes = {
            "ASSAMESE": "as", "BENGALI": "bn", "BODO": "brx", "DOGRI": "doi", 
            "GUJARATI": "gu", "HINDI": "hi", "KANNADA": "kn", "KASHMIRI": "ks", 
            "KONKANI": "gom", "MAITHILI": "mai", "MALAYALAM": "ml", "MANIPURI": "mni", 
            "MARATHI": "mr", "NEPALI": "ne", "ODIA": "or", "PUNJABI": "pa", 
            "SANSKRIT": "sa", "SANTALI": "sat", "SINDHI": "sd", "TAMIL": "ta", 
            "TELUGU": "te", "URDU": "ur"
        }
        
        req_lang_upper = requested_language.upper()
        if req_lang_upper != "ENGLISH" and req_lang_upper in bhashini_lang_codes:
            target_code = bhashini_lang_codes[req_lang_upper]
            llm_text = await translate_with_bhashini(llm_text, source_lang="en", target_lang=target_code)
            if disclaimer:
                disclaimer = await translate_with_bhashini(disclaimer, source_lang="en", target_lang=target_code)

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