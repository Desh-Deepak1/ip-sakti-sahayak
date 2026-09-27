from pydantic import BaseModel, Field
from typing import List

class Claim(BaseModel):
    claim_text: str
    evidence_ids: List[str]

class StructuredLLMResponse(BaseModel):
    claims: List[Claim]
    assessment: str
    next_actions: List[str]
    risk_flags: List[str]
    abstain: bool