"""
main.py — CareFlow Backend API
Run with: uvicorn main:app --reload --port 8000
"""

import time
import os
import sys

# Add parent directory to path so agents/tools can be imported
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from tools.fhir_parser import get_all_patient_summaries, get_patient_by_id, build_patient_summary
from tools.rag_engine import retrieve_guidelines
from agents.orchestrator import route_query
import agents.patient_navigator as patient_navigator
import agents.care_coordinator as care_coordinator
import agents.quality_analyst as quality_analyst
import agents.ai_nurse as ai_nurse

# ─── App Setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CareFlow API",
    description="Multi-Agent Clinical Workflow Orchestration System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Agent Registry ───────────────────────────────────────────────────────────
AGENT_REGISTRY = {
    "patient_navigator": patient_navigator.run,
    "care_coordinator": care_coordinator.run,
    "quality_analyst": quality_analyst.run,
    "ai_nurse": ai_nurse.run,
}

# ─── Request/Response Models ─────────────────────────────────────────────────
class QueryRequest(BaseModel):
    patient_id: str
    query: str

class EvalLog(BaseModel):
    patient_id: str
    query: str
    selected_agent: str
    confidence: float
    latency_ms: float
    task_completion: str


# ─── In-Memory Eval Log ───────────────────────────────────────────────────────
eval_logs: list[EvalLog] = []


# ─── Routes ──────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "CareFlow API is running", "docs": "/docs"}


@app.get("/patients")
def get_patients():
    """Return all patients for the dashboard."""
    return get_all_patient_summaries()


@app.get("/patients/{patient_id}")
def get_patient(patient_id: str):
    """Return full patient record."""
    patient = get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@app.post("/query")
def handle_query(request: QueryRequest):
    """
    Main endpoint: Orchestrates routing and agent execution.
    1. Orchestrator decides which agent to use
    2. Selected agent runs and returns structured response
    3. Evaluation metrics logged
    """
    start_time = time.time()

    # Step 1: Route
    routing_result = route_query(request.patient_id, request.query)

    if "error" in routing_result:
        raise HTTPException(status_code=404, detail=routing_result["error"])

    routing = routing_result["routing"]
    selected_agent = routing.get("selected_agent", "care_coordinator")
    patient_summary = routing_result["patient_summary"]
    guidelines = routing_result["guidelines_used"]

    # Step 2: Run selected agent
    agent_fn = AGENT_REGISTRY.get(selected_agent, care_coordinator.run)
    agent_response = agent_fn(patient_summary, request.query, guidelines)

    # Step 3: Log evaluation
    latency_ms = (time.time() - start_time) * 1000
    task_completion = agent_response.get("evaluation", {}).get("task_completion", "unknown")
    agent_confidence = agent_response.get("evaluation", {}).get("confidence", routing.get("confidence", 0.5))

    log = EvalLog(
        patient_id=request.patient_id,
        query=request.query,
        selected_agent=selected_agent,
        confidence=agent_confidence,
        latency_ms=round(latency_ms, 2),
        task_completion=task_completion
    )
    eval_logs.append(log)

    return {
        "orchestrator": {
            "selected_agent": selected_agent,
            "routing_reason": routing.get("routing_reason"),
            "confidence": routing.get("confidence"),
            "urgency": routing.get("urgency"),
        },
        "agent_response": agent_response,
        "guidelines_used": guidelines,
        "evaluation": {
            "latency_ms": round(latency_ms, 2),
            "task_completion": task_completion,
            "confidence": agent_confidence,
        },
        "patient": routing_result["patient"]
    }


@app.get("/eval/logs")
def get_eval_logs():
    """Return all evaluation logs."""
    return [log.dict() for log in eval_logs]


@app.get("/eval/summary")
def get_eval_summary():
    """Return evaluation summary metrics."""
    if not eval_logs:
        return {"message": "No queries run yet"}

    avg_latency = sum(l.latency_ms for l in eval_logs) / len(eval_logs)
    avg_confidence = sum(l.confidence for l in eval_logs) / len(eval_logs)
    completion_counts = {}
    agent_counts = {}

    for log in eval_logs:
        completion_counts[log.task_completion] = completion_counts.get(log.task_completion, 0) + 1
        agent_counts[log.selected_agent] = agent_counts.get(log.selected_agent, 0) + 1

    return {
        "total_queries": len(eval_logs),
        "avg_latency_ms": round(avg_latency, 2),
        "avg_confidence": round(avg_confidence, 3),
        "task_completion_breakdown": completion_counts,
        "agent_usage": agent_counts,
    }
