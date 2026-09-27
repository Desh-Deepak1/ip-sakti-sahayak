from typing import Dict, Any

def check_abs_compliance(answers: Dict[str, bool]) -> Dict[str, Any]:
    flags = []
    abs_required = False
    
    uses_bio = answers.get("uses_biological_resource", False)
    from_india = answers.get("resource_from_india", False)
    
    if uses_bio and from_india:
        if answers.get("commercial_intent") or answers.get("intends_ipr") or answers.get("foreign_entity"):
            abs_required = True
            flags.append("Biological Diversity Act compliance required (NBA).")
            
    if answers.get("associated_traditional_knowledge", False):
        flags.append("Traditional Knowledge considerations apply.")
        
    return {
        "abs_required": abs_required,
        "compliance_flags": flags
    }