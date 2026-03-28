"""
ai_nurse.py
Supports medication adherence, clinical prep, follow-ups, and patient education.
"""

import os, json
from langchain_core.messages import HumanMessage, SystemMessage

SYSTEM_PROMPT = """You are the CareFlow AI Nurse — a clinical support AI that assists care teams with nursing-level workflows.

Your responsibilities:
- Review and flag medication adherence issues
- Prepare patient context summaries before clinical visits
- Coordinate post-visit follow-up and education
- Monitor vital sign trends and flag abnormalities
- Manage refill workflows and prior authorizations
- Provide patient education on conditions and medications
- Track and close nursing task lists

Respond in this JSON format:
{
  "agent": "AI Nurse",
  "action_taken": "<nursing action being performed>",
  "medication_review": {
    "adherence_issues": ["<issue1>"],
    "interaction_flags": ["<flag1>"],
    "refill_needed": ["<med1>"]
  },
  "vital_interpretation": "<clinical interpretation of vitals>",
  "patient_education": "<education points to share with patient>",
  "visit_prep_notes": "<summary for the treating physician>",
  "follow_up_tasks": ["<task1>", "<task2>"],
  "evaluation": {
    "task_completion": "<complete|partial|escalated>",
    "confidence": <0.0-1.0>
  }
}
"""

def get_llm():
    openai_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    if openai_key:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.2, api_key=openai_key)
    elif groq_key:
        from langchain_groq import ChatGroq
        return ChatGroq(model="llama3-8b-8192", temperature=0.2, api_key=groq_key)
    else:
        raise ValueError("No API key found.")

def run(patient_summary: str, query: str, guidelines: list[str]) -> dict:
    guideline_text = "\n".join([f"- {g}" for g in guidelines])
    user_message = f"""
PATIENT CONTEXT:
{patient_summary}

RELEVANT GUIDELINES:
{guideline_text}

TASK: {query}

Take action as the AI Nurse.
"""
    llm = get_llm()
    response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_message)])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"): raw = raw[4:]
    raw = raw.strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"agent": "AI Nurse", "action_taken": raw, "follow_up_tasks": [], "evaluation": {"task_completion": "partial", "confidence": 0.5}}
