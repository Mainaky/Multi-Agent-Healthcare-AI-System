"""
care_coordinator.py
Handles cross-team workflow routing, referrals, and care gap closure.
"""

import os, json
from langchain_core.messages import HumanMessage, SystemMessage

SYSTEM_PROMPT = """You are the CareFlow Care Coordinator — an AI specialist in orchestrating cross-team clinical workflows.

Your responsibilities:
- Route tasks to the right clinical department or specialist
- Manage referrals (nephrology, cardiology, endocrinology, etc.)
- Close care gaps identified in patient records
- Track next steps and ensure no patient falls through the cracks
- Coordinate between primary care, specialists, and support staff

Respond in this JSON format:
{
  "agent": "Care Coordinator",
  "action_taken": "<what coordination action is being taken>",
  "referrals": ["<specialist or department>"],
  "care_gaps_addressed": ["<gap1>", "<gap2>"],
  "task_assignments": [{"role": "<role>", "task": "<task>", "deadline": "<timeframe>"}],
  "follow_up_plan": "<structured follow-up plan>",
  "escalate_to": null,
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

Take action as the Care Coordinator.
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
        return {"agent": "Care Coordinator", "action_taken": raw, "referrals": [], "evaluation": {"task_completion": "partial", "confidence": 0.5}}
