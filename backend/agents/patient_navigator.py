"""
patient_navigator.py
Handles scheduling, refills, follow-ups, and patient engagement.
"""

import os
from langchain_core.messages import HumanMessage, SystemMessage


SYSTEM_PROMPT = """You are the CareFlow Patient Navigator — an AI assistant specialized in patient access and engagement.

Your responsibilities:
- Schedule and reschedule appointments
- Manage prescription refill requests
- Coordinate follow-up visits
- Handle patient intake and onboarding
- Identify and remove barriers to care access (transport, cost, language)
- Send engagement reminders and check-ins

Guidelines to follow:
- Always prioritize patient convenience and access
- Offer telehealth as an alternative when appropriate
- For missed follow-ups, identify root cause before rescheduling
- Document all actions taken

Respond in this JSON format:
{
  "agent": "Patient Navigator",
  "action_taken": "<what you are doing for the patient>",
  "steps": ["step1", "step2", "step3"],
  "next_appointment": "<suggested date/timeframe>",
  "patient_message": "<a warm, empathetic message to send the patient>",
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
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.3, api_key=openai_key)
    elif groq_key:
        from langchain_groq import ChatGroq
        return ChatGroq(model="llama3-8b-8192", temperature=0.3, api_key=groq_key)
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

Take action as the Patient Navigator.
"""
    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ])
    import json
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"agent": "Patient Navigator", "action_taken": raw, "steps": [], "evaluation": {"task_completion": "partial", "confidence": 0.5}}
