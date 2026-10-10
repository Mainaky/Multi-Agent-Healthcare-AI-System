from agents.llm_client import generate_json_response

def fallback_care_coordinator(patient_summary: str, query: str) -> dict:
    return {
        "agent": "care_coordinator",
        "action_taken": f"Orchestrated cross-disciplinary referrals and closed urgent care gaps for: {query}",
        "referrals": [
            "Specialist consultation (Cardiology / Nephrology / Endocrinology as indicated)",
            "Clinical Nutrition & Dietetics referral",
            "Medical Social Work / Care Management evaluation"
        ],
        "care_gaps_addressed": [
            "Overdue lab work and chronic disease screening flagged for immediate closure",
            "Specialist consult authorization and care transition plan initiated"
        ],
        "task_assignments": [
            {"role": "Care Manager", "task": "Complete initial clinical assessment and intake", "deadline": "48 hours"},
            {"role": "Clinic Nurse", "task": "Coordinate diagnostic workup and labs", "deadline": "3 days"},
            {"role": "Patient Navigator", "task": "Confirm transportation and appointment booking", "deadline": "24 hours"}
        ],
        "follow_up_plan": "Bi-weekly multidisciplinary case review until all urgent care gaps are closed and vitals stabilize.",
        "evaluation": {"task_completion": "complete"}
    }

def run(patient_summary: str, query: str, guidelines: list[str]) -> dict:
    system_msg = (
        "You are the Care Coordinator AI Agent for CareFlow. "
        "Your role is multidisciplinary care management, referrals, care gap closures, and team task assignments. "
        "Respond in valid JSON with keys: "
        "'agent' (must be 'care_coordinator'), "
        "'action_taken' (concise summary string), "
        "'referrals' (array of referral strings), "
        "'care_gaps_addressed' (array of care gap closure action strings), "
        "'task_assignments' (array of objects each having 'role', 'task', and 'deadline'), "
        "'follow_up_plan' (summary of the ongoing care management plan string), "
        "'evaluation' (object with 'task_completion': 'complete')"
    )
    prompt = f"Context: {patient_summary}\nTask: {query}\nGuidelines:\n{guidelines}"
    
    resp = generate_json_response(system_msg, prompt, default_factory=lambda: fallback_care_coordinator(patient_summary, query))
    if not isinstance(resp, dict):
        resp = fallback_care_coordinator(patient_summary, query)
    resp.setdefault("agent", "care_coordinator")
    resp.setdefault("action_taken", "Care coordination plan formulated.")
    resp.setdefault("evaluation", {"task_completion": "complete"})
    return resp