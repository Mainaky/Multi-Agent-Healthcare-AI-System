"""
fhir_parser.py
Parses synthetic FHIR-like patient records and returns structured summaries.
"""

import json
import os
from pathlib import Path


DATA_PATH = Path(__file__).parent.parent / "data" / "patients.json"


def load_all_patients() -> list[dict]:
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def get_patient_by_id(patient_id: str) -> dict | None:
    patients = load_all_patients()
    for p in patients:
        if p["id"] == patient_id:
            return p
    return None


def build_patient_summary(patient: dict) -> str:
    """Convert patient dict into a clinical text summary for the LLM."""
    care_gaps = "\n  - ".join(patient.get("care_gaps", []))
    meds = ", ".join(patient.get("medications", []))
    labs = patient.get("lab_results", {})
    lab_str = ", ".join([f"{k}: {v}" for k, v in labs.items()])

    return f"""
PATIENT SUMMARY
===============
Name: {patient['name']} | Age: {patient['age']} | Gender: {patient['gender']}
Condition: {patient['condition']}
Risk Score: {patient['risk_score']} / 1.0
Missed Follow-ups: {patient['missed_followups']}
Last Visit: {patient['last_visit']}
Next Appointment: {patient.get('next_appointment', 'Not scheduled')}

Medications: {meds}

Lab Results: {lab_str}

Active Care Gaps:
  - {care_gaps}

Clinical Notes: {patient.get('notes', 'None')}
Insurance: {patient.get('insurance', 'Unknown')}
""".strip()


def get_all_patient_summaries() -> list[dict]:
    """Return list of {id, name, risk_score, condition} for dashboard."""
    patients = load_all_patients()
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "age": p["age"],
            "condition": p["condition"],
            "risk_score": p["risk_score"],
            "missed_followups": p["missed_followups"],
            "care_gaps_count": len(p.get("care_gaps", [])),
        }
        for p in patients
    ]
