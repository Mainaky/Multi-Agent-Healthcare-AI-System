"""
orchestrator.py
Master routing agent — decides which specialist agent handles the query.
"""

import os
import json
from langchain_core.messages import HumanMessage, SystemMessage
from tools.fhir_parser import build_patient_summary, get_patient_by_id
from tools.rag_engine import retrieve_guidelines, format_guidelines_for_prompt


AGENT_DESCRIPTIONS = {
    "patient_navigator": "Handles scheduling, appointment rescheduling, refills, follow-up booking, intake, and patient engagement tasks.",
    "care_coordinator": "Handles cross-team workflow routing, referrals, care gap closure, task assignment between departments, and multi-provider coordination.",
    "quality_analyst": "Handles risk scoring, quality measure gaps, compliance monitoring, documentation issues, and safety flag generation.",
    "ai_nurse": "Handles medication adherence, clinical preparation, patient education, vital sign interpretation, and nursing support tasks.",
}


ORCHESTRATOR_SYSTEM = """You are the CareFlow Orchestrator — a master clinical routing AI.

Your ONLY job is to analyze the patient context and user query, then decide which specialist agent should handle it.

Available agents:
{agent_list}

Respond ONLY with a valid JSON object in this exact format:
{{
  "selected_agent": "<agent_name>",
  "routing_reason": "<1-2 sentence explanation>",
  "confidence": <0.0 to 1.0>,
  "urgency": "<low|medium|high|critical>"
}}

Do not add any other text. Only return the JSON.
"""


def get_llm():
    """Load LLM based on available API keys."""
    openai_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    if openai_key:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=openai_key)
    elif groq_key:
        from langchain_groq import ChatGroq
        return ChatGroq(model="llama3-8b-8192", temperature=0.1, api_key=groq_key)
    else:
        raise ValueError("No API key found. Set OPENAI_API_KEY or GROQ_API_KEY in .env file.")


def route_query(patient_id: str, query: str) -> dict:
    """
    Routes a clinical query to the appropriate specialist agent.
    Returns routing decision + patient context.
    """
    patient = get_patient_by_id(patient_id)
    if not patient:
        return {"error": f"Patient {patient_id} not found"}

    patient_summary = build_patient_summary(patient)

    # RAG: retrieve relevant guidelines
    guidelines = retrieve_guidelines(query + " " + patient.get("condition", ""))
    guideline_text = format_guidelines_for_prompt(guidelines)

    agent_list = "\n".join(
        [f"- {k}: {v}" for k, v in AGENT_DESCRIPTIONS.items()]
    )

    system_prompt = ORCHESTRATOR_SYSTEM.format(agent_list=agent_list)

    user_message = f"""
PATIENT CONTEXT:
{patient_summary}

RELEVANT CLINICAL GUIDELINES:
{guideline_text}

USER QUERY: {query}

Route this to the most appropriate agent.
"""

    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ])

    raw = response.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        routing = json.loads(raw)
    except Exception:
        routing = {
            "selected_agent": "care_coordinator",
            "routing_reason": "Could not parse routing decision. Defaulting to Care Coordinator.",
            "confidence": 0.5,
            "urgency": "medium"
        }

    return {
        "routing": routing,
        "patient": patient,
        "patient_summary": patient_summary,
        "guidelines_used": guidelines,
        "query": query
    }
