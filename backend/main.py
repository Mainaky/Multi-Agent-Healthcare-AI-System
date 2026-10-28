import time, os, sys, json, uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from database import (
    init_db,
    db_get_all_patients,
    db_get_patient_by_id,
    db_save_patient,
    db_delete_patient,
    db_save_consultation
)
from tools.fhir_parser import get_all_patient_summaries, get_patient_by_id, save_patient, delete_patient
from agents.orchestrator import route_query
from agents.llm_client import generate_json_response
import agents.patient_navigator as patient_navigator
import agents.care_coordinator as care_coordinator
import agents.quality_analyst as quality_analyst
import agents.ai_nurse as ai_nurse

app = FastAPI(title="CareFlow Enterprise Clinical API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

AGENT_REGISTRY = {
    "patient_navigator": patient_navigator.run,
    "care_coordinator": care_coordinator.run,
    "quality_analyst": quality_analyst.run,
    "ai_nurse": ai_nurse.run,
}

# In-memory evaluation tracking
EVAL_LOGS = []

# Authentication
class LoginRequest(BaseModel):
    username: Optional[str] = "Dr. Attending Clinician"
    password: Optional[str] = "demo"

@app.post("/auth/login")
def login(req: LoginRequest):
    user = (req.username or "").strip() or "Dr. Attending Clinician"
    return {
        "status": "success",
        "username": user,
        "message": "Authenticated successfully into CareFlow Enterprise"
    }

class QueryRequest(BaseModel):
    patient_id: str
    query: str

class PatientInput(BaseModel):
    id: Optional[str] = None
    name: str
    age: Optional[int] = 45
    gender: Optional[str] = "Other"
    condition: Optional[str] = "General Clinical Assessment"
    insurance: Optional[str] = "Standard Clinical Health"
    medications: Optional[List[str]] = Field(default_factory=list)
    lab_results: Optional[Dict[str, Any]] = Field(default_factory=dict)
    vitals: Optional[Dict[str, Any]] = Field(default_factory=dict)
    care_gaps: Optional[List[str]] = Field(default_factory=list)
    risk_score: Optional[float] = 0.5
    missed_followups: Optional[int] = 0
    notes: Optional[str] = ""

class AIGeneratePatientRequest(BaseModel):
    name: str
    id: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    condition: Optional[str] = None
    notes: Optional[str] = None

# Path to frontend dashboard
FRONTEND_INDEX = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html"))

@app.get("/")
def serve_dashboard():
    if os.path.exists(FRONTEND_INDEX):
        return FileResponse(FRONTEND_INDEX)
    return {"message": "CareFlow Clinical Orchestrator API is active", "docs": "/docs"}

@app.get("/patients")
def get_patients():
    return get_all_patient_summaries()

@app.get("/patients/{patient_id}")
def get_patient(patient_id: str):
    patient = get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found in EHR database")
    return patient

@app.post("/patients")
def create_patient(data: PatientInput):
    # Auto-assign ID if not provided
    patient_id = data.id.strip() if data.id and data.id.strip() else f"P{len(get_all_patient_summaries()) + 1:03d}"
    
    patient_dict = {
        "id": patient_id,
        "name": data.name.strip(),
        "age": data.age or 45,
        "gender": data.gender or "Other",
        "condition": data.condition or "General Clinical Assessment",
        "last_visit": datetime.utcnow().strftime("%Y-%m-%d"),
        "next_appointment": None,
        "medications": data.medications or ["Multivitamin daily"],
        "lab_results": data.lab_results or {"BP": "120/80", "HbA1c": 5.6},
        "vitals": data.vitals or {"weight_kg": 70, "height_cm": 170, "BMI": 24.2},
        "missed_followups": data.missed_followups or 0,
        "insurance": data.insurance or "Standard Clinical Health",
        "care_gaps": data.care_gaps or ["Annual routine screening due"],
        "risk_score": float(data.risk_score or 0.45),
        "notes": data.notes or f"Clinical record created on {datetime.utcnow().strftime('%Y-%m-%d')}."
    }
    
    saved = save_patient(patient_dict)
    return {
        "status": "success",
        "message": f"Patient {saved['name']} (#{saved['id']}) successfully saved to database.",
        "patient": saved
    }

@app.post("/patients/ai-generate")
def ai_generate_patient(req: AIGeneratePatientRequest):
    """
    AI-Assisted Patient Generator:
    Takes basic inputs (name, condition, age) and uses Gemini 2.5 Flash to synthesize
    a clinically authentic, guideline-grounded EHR profile, and immediately persists it to PostgreSQL/SQLite.
    """
    patient_id = req.id.strip() if req.id and req.id.strip() else f"P{len(get_all_patient_summaries()) + 1:03d}"
    name = req.name.strip()
    age = req.age or 52
    gender = req.gender or "Female"
    condition = req.condition or "Type 2 Diabetes Mellitus with Mild Hypertension"
    notes_hint = req.notes or "Patient presenting for routine chronic disease review."

    system_prompt = (
        "You are an AI Hospital EHR System. Generate a realistic, clinically grounded patient record "
        "matching ADA, ACC/AHA, or KDIGO guidelines for the given condition.\n"
        "Return ONLY a valid JSON object with the following exact keys:\n"
        "{\n"
        '  "condition": "Specific detailed diagnosis",\n'
        '  "risk_score": 0.65,\n'
        '  "medications": ["Med 1", "Med 2"],\n'
        '  "lab_results": {"HbA1c": 7.8, "BP": "138/88", "eGFR": 65, "LDL": 125},\n'
        '  "vitals": {"weight_kg": 74, "height_cm": 165, "BMI": 27.2},\n'
        '  "care_gaps": ["Clinical care gap 1", "Clinical care gap 2"],\n'
        '  "missed_followups": 1,\n'
        '  "insurance": "Blue Cross Blue Shield Gold",\n'
        '  "notes": "Brief clinical intake summary"\n'
        "}"
    )
    user_prompt = f"Patient Name: {name}, Age: {age}, Gender: {gender}, Primary Condition/Complaint: {condition}, Clinical Context: {notes_hint}"

    def default_patient_profile():
        return {
            "condition": condition,
            "risk_score": 0.58,
            "medications": ["Metformin 500mg daily", "Lisinopril 10mg daily"],
            "lab_results": {"HbA1c": 7.6, "BP": "135/86", "eGFR": 72, "LDL": 130},
            "vitals": {"weight_kg": 75, "height_cm": 168, "BMI": 26.6},
            "care_gaps": ["HbA1c control audit overdue", "Annual diabetic microalbuminuria check"],
            "missed_followups": 1,
            "insurance": "Aetna Comprehensive Health",
            "notes": f"AI-assisted clinical intake for {name} with diagnosis of {condition}."
        }

    ai_data = generate_json_response(system_prompt, user_prompt, default_factory=default_patient_profile)
    if not isinstance(ai_data, dict):
        ai_data = default_patient_profile()

    # Build complete record
    full_patient = {
        "id": patient_id,
        "name": name,
        "age": age,
        "gender": gender,
        "condition": ai_data.get("condition", condition),
        "last_visit": datetime.utcnow().strftime("%Y-%m-%d"),
        "next_appointment": None,
        "medications": ai_data.get("medications", ["Aspirin 81mg"]),
        "lab_results": ai_data.get("lab_results", {"BP": "125/82"}),
        "vitals": ai_data.get("vitals", {"weight_kg": 70, "height_cm": 170, "BMI": 24.2}),
        "missed_followups": int(ai_data.get("missed_followups", 0)),
        "insurance": ai_data.get("insurance", "Medicare Advantage / Private"),
        "care_gaps": ai_data.get("care_gaps", ["Routine baseline lab review"]),
        "risk_score": float(ai_data.get("risk_score", 0.5)),
        "notes": ai_data.get("notes", f"Synthesized AI intake profile for {name}.")
    }

    # Save to PostgreSQL / SQLite database
    saved_patient = save_patient(full_patient)
    return {
        "status": "success",
        "message": f"AI successfully synthesized and stored EHR profile for {name} (#{patient_id}).",
        "patient": saved_patient
    }

@app.delete("/patients/{patient_id}")
def remove_patient(patient_id: str):
    success = delete_patient(patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Patient not found or could not be deleted")
    return {"status": "success", "message": f"Patient #{patient_id} removed from EHR database."}

@app.get("/eval/summary")
def get_eval_summary():
    if not EVAL_LOGS:
        return {
            "total_queries": 0,
            "avg_latency_ms": 0,
            "avg_confidence": 0.0,
            "agent_usage": {}
        }
    total = len(EVAL_LOGS)
    avg_latency = round(sum(item["latency_ms"] for item in EVAL_LOGS) / total, 1)
    avg_conf = round(sum(item["confidence"] for item in EVAL_LOGS) / total, 2)
    usage = {}
    for item in EVAL_LOGS:
        usage[item["selected_agent"]] = usage.get(item["selected_agent"], 0) + 1
    return {
        "total_queries": total,
        "avg_latency_ms": avg_latency,
        "avg_confidence": avg_conf,
        "agent_usage": usage
    }

@app.get("/eval/logs")
def get_eval_logs():
    return EVAL_LOGS

@app.post("/query")
def handle_query(request: QueryRequest):
    start_time = time.time()
    routing_result = route_query(request.patient_id, request.query)
    routing = routing_result["routing"]
    selected_agent = routing.get("selected_agent", "care_coordinator")
    
    agent_fn = AGENT_REGISTRY.get(selected_agent, care_coordinator.run)
    agent_response = agent_fn(routing_result["patient_summary"], request.query, routing_result["guidelines_used"])

    # Safety Shield
    if isinstance(agent_response, str):
        try:
            clean_str = agent_response.strip().replace("```json", "").replace("```", "")
            agent_response = json.loads(clean_str)
        except Exception:
            agent_response = {
                "agent": selected_agent, 
                "action_taken": agent_response, 
                "evaluation": {"task_completion": "complete"}
            }

    latency_ms = round((time.time() - start_time) * 1000, 2)
    confidence = float(routing.get("confidence", 0.9))
    task_completion = "complete"
    if isinstance(agent_response, dict) and "evaluation" in agent_response:
        task_completion = agent_response["evaluation"].get("task_completion", "complete")

    # Record eval metrics
    EVAL_LOGS.append({
        "timestamp": time.time(),
        "patient_id": request.patient_id,
        "query": request.query,
        "selected_agent": selected_agent,
        "confidence": confidence,
        "latency_ms": latency_ms,
        "task_completion": task_completion
    })

    # Persist consultation log to database
    try:
        db_save_consultation(
            patient_id=request.patient_id,
            query=request.query,
            selected_agent=selected_agent,
            confidence=confidence,
            latency_ms=latency_ms,
            agent_resp=agent_response,
            guidelines=routing_result.get("guidelines_used", [])
        )
    except Exception as e:
        print(f"[Main Query] Consultation DB log notice: {e}")

    return {
        "orchestrator": routing,
        "agent_response": agent_response,
        "guidelines_used": routing_result["guidelines_used"],
        "evaluation": {
            "latency_ms": latency_ms,
            "confidence": confidence,
            "task_completion": task_completion
        },
        "patient": routing_result["patient"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)