import json, os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "patients.json"

try:
    from database import db_get_all_patients, db_get_patient_by_id, db_save_patient, db_delete_patient
except ImportError:
    import sys
    sys.path.insert(0, str(BASE_DIR))
    from database import db_get_all_patients, db_get_patient_by_id, db_save_patient, db_delete_patient

def load_all_patients() -> list[dict]:
    try:
        patients = db_get_all_patients()
        if patients:
            return patients
    except Exception as e:
        print(f"[FHIR Parser] DB read fallback: {e}")
    
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_patient_by_id(patient_id: str) -> dict | None:
    try:
        p = db_get_patient_by_id(patient_id)
        if p:
            return p
    except Exception as e:
        print(f"[FHIR Parser] DB get patient fallback: {e}")
    
    patients = load_all_patients()
    return next((p for p in patients if str(p.get("id")).strip() == str(patient_id).strip()), None)

def save_patient(patient_data: dict) -> dict:
    return db_save_patient(patient_data)

def delete_patient(patient_id: str) -> bool:
    return db_delete_patient(patient_id)

def get_all_patient_summaries() -> list[dict]:
    patients = load_all_patients()
    return [{
        "id": p["id"],
        "name": p["name"],
        "age": p["age"],
        "gender": p.get("gender", "Other"),
        "condition": p.get("condition") or ", ".join(p.get("conditions", [])),
        "insurance": p.get("insurance", "Standard Health"),
        "risk_score": p.get("risk_score", 0.5),
        "lab_results": p.get("lab_results", {}),
        "care_gaps": p.get("care_gaps", []),
        "missed_followups": p.get("missed_followups", 0),
        "last_visit": p.get("last_visit", "Recent")
    } for p in patients]

def build_patient_summary(patient: dict) -> str:
    if not patient:
        return "No clinical data available."
    meds = ", ".join(patient.get("medications", [])) if patient.get("medications") else "None"
    gaps = ", ".join(patient.get("care_gaps", [])) if patient.get("care_gaps") else "None"
    labs = ", ".join([f"{k}: {v}" for k, v in patient.get("lab_results", {}).items()]) if patient.get("lab_results") else "None"
    
    return (
        f"Patient: {patient.get('name')} (MRN: {patient.get('id')}), {patient.get('age')}yo {patient.get('gender')}.\n"
        f"Condition: {patient.get('condition')}.\n"
        f"Vitals/Labs: {labs}.\n"
        f"Active Medications: {meds}.\n"
        f"Care Gaps: {gaps}.\n"
        f"Missed Follow-ups: {patient.get('missed_followups', 0)}.\n"
        f"Risk Score: {patient.get('risk_score', 0.5)}."
    )