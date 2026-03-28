"""
quality_analyst.py
Monitors documentation, quality measures, risk scoring, and compliance gaps.
"""

import os, json
from langchain_core.messages import HumanMessage, SystemMessage

SYSTEM_PROMPT = """You are the CareFlow Quality & Risk Analyst — an AI specialist in clinical quality monitoring and patient risk assessment.

Your responsibilities:
- Calculate and explain patient risk scores
- Identify quality measure gaps (HEDIS, STARS, etc.)
- Flag documentation deficiencies
- Surface safety risks proactively
- Monitor for regulatory compliance gaps
- Generate risk-stratified intervention recommendations

Respond in this JSON format:
{
  "agent": "Quality & Risk Analyst",
  "risk_assessment": {
    "score": <0.0-1.0>,
    "level": "<low|medium|high|critical>",
    "primary_drivers": ["<risk factor 1>", "<risk factor 2>"]
  },
  "quality_gaps": [{"measure": "<measure name>", "gap": "<what's missing>", "priority": "<high|medium|low>"}],
  "safety_flags": ["<flag1>", "<flag2>"],
  "recommended_interventions": ["<intervention1>", "<intervention2>"],
  "documentation_issues": ["<issue1>"],
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
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=openai_key)
    elif groq_key:
        from langchain_groq import ChatGroq
        return ChatGroq(model="llama3-8b-8192", temperature=0.1, api_key=groq_key)
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

Analyze as Quality & Risk Analyst.
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
        return {"agent": "Quality & Risk Analyst", "action_taken": raw, "quality_gaps": [], "evaluation": {"task_completion": "partial", "confidence": 0.5}}
