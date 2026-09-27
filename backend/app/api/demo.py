from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(prefix="/api/v1", tags=["Demo"])

@router.get("/demo/scenario")
async def get_demo_scenario() -> Dict[str, Any]:
    return {
        "scenario_title": "Ashwagandha and Tulsi Herbal Formulation Patent Evaluation",
        "query": "I developed a new herbal formulation containing Ashwagandha and Tulsi. Can I patent it?",
        "classification_flow": [
            {"step": 1, "question": "Is this formulation directly described in an authoritative Ayurvedic text?", "answer": "No"},
            {"step": 2, "question": "What is new (composition, extraction method, manufacturing process, or therapeutic use)?", "answer": "New extraction process."},
            {"step": 3, "determination": "Potentially patent-relevant technical innovation identified."}
        ],
        "regulatory_category": "PROPRIETARY_AYURVEDA",
        "jurisdiction": "INDIA",
        "ip_pathways": ["PATENT", "TRADEMARK", "TRADE_SECRET"],
        "abs_indicators": {"uses_biological_resource": True, "resource_from_india": True, "abs_required": True},
        "evidence_score": {"score": 0.85, "rating": "High Evidence", "abstain": False},
        "citations": ["Patents Act, 1970 - Section 3(p)", "Biological Diversity Rules, 2024"],
        "disclaimer": "Information, not legal advice."
    }