import json, os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "patients.json"

def load_all_patients():
    if not DATA_PATH.exists(): return []
    with open(DATA_PATH, "r", encoding="utf-8") as f: return json.load(f)

def get_patient_by_id(patient_id: str):
    patients = load_all_patients()
    return next((p for p in patients if str(p.get("id")).strip() == str(patient_id).strip()), None)

def get_all_patient_summaries():
    patients = load_all_patients()
    return [{"id": p["id"], "name": p["name"], "age": p["age"], "condition": p.get("condition") or ", ".join(p.get("conditions", []))} for p in patients]

def build_patient_summary(patient: dict):
    if not patient: return "No data."
    return f"Patient {patient.get('name')}, {patient.get('age')}y. Diagnosis: {patient.get('condition')}."