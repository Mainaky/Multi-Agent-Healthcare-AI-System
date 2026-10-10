import os
import json
from tools.fhir_parser import build_patient_summary, get_patient_by_id
from tools.rag_engine import retrieve_guidelines
from agents.llm_client import generate_json_response

def fallback_router(query: str) -> dict:
    q = query.lower()
    if any(k in q for k in ["schedule", "appointment", "missed", "reschedule", "intake", "follow-up", "book"]):
        return {
            "selected_agent": "patient_navigator",
            "routing_reason": "Query pertains to scheduling, appointments, or patient outreach navigation.",
            "confidence": 0.88,
            "urgency": "medium"
        }
    elif any(k in q for k in ["bnp", "risk", "score", "flag", "compliance", "chf", "egfr", "decline"]):
        return {
            "selected_agent": "quality_analyst",
            "routing_reason": "Query involves clinical risk scoring, deterioration metrics, or safety assessment.",
            "confidence": 0.92,
            "urgency": "high"
        }
    elif any(k in q for k in ["medication", "meds", "refill", "iron", "hba1c", "prep", "dose", "drug", "inhaler"]):
        return {
            "selected_agent": "ai_nurse",
            "routing_reason": "Query relates to medication review, clinical education, or adherence.",
            "confidence": 0.90,
            "urgency": "medium"
        }
    else:
        return {
            "selected_agent": "care_coordinator",
            "routing_reason": "General care coordination, referral management, or care gap closure.",
            "confidence": 0.85,
            "urgency": "medium"
        }

def route_query(patient_id: str, query: str) -> dict:
    patient = get_patient_by_id(patient_id)
    patient_summary = build_patient_summary(patient)
    guidelines = retrieve_guidelines(query)
    
    system_msg = (
        "You are a clinical orchestrator in an AI hospital system. "
        "Analyze the patient context and clinical query, and route to the most appropriate agent: "
        "'patient_navigator' (scheduling, intake, appointments, outreach), "
        "'care_coordinator' (referrals, care gap closure, multidisciplinary tasks), "
        "'quality_analyst' (risk scoring, safety flags, compliance gaps), or "
        "'ai_nurse' (medication adherence, vital signs prep, clinical education). "
        "Respond ONLY in valid JSON format: "
        '{"selected_agent": "...", "routing_reason": "...", "confidence": 0.95, "urgency": "low|medium|high|critical"}'
    )
    prompt = f"Patient: {patient_summary}\nQuery: {query}\nGuidelines: {guidelines}"
    
    routing = generate_json_response(system_msg, prompt, default_factory=lambda: fallback_router(query))
    
    # Ensure all required fields are present
    if "selected_agent" not in routing or routing["selected_agent"] not in ["patient_navigator", "care_coordinator", "quality_analyst", "ai_nurse"]:
        routing["selected_agent"] = fallback_router(query)["selected_agent"]
    if "routing_reason" not in routing:
        routing["routing_reason"] = "Clinical context matched agent domain."
    if "confidence" not in routing:
        routing["confidence"] = 0.9
    if "urgency" not in routing:
        routing["urgency"] = "medium"

    return {
        "routing": routing,
        "patient": patient,
        "patient_summary": patient_summary,
        "guidelines_used": guidelines
    }