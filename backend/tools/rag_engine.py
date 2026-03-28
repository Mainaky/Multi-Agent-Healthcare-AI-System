"""
rag_engine.py - Zero dependency keyword-based retrieval (no numpy, no faiss, no transformers)
Works on any Python version on Windows without crashes.
"""

import re

CLINICAL_GUIDELINES = [
    "ADA 2024: HbA1c target for most adults with Type 2 Diabetes is <7%. Values >8% indicate poor control requiring medication adjustment or lifestyle intervention.",
    "JNC 8: Blood pressure target for diabetic patients is <140/90 mmHg. Persistent hypertension requires ACE inhibitor or ARB as first-line therapy.",
    "AHA 2023: Patients with CHF and reduced EF (<40%) should be on beta-blockers, ACE inhibitors/ARBs, and diuretics. BNP >400 pg/mL warrants urgent evaluation.",
    "KDIGO 2022: eGFR <30 mL/min requires nephrology referral. Avoid NSAIDs and nephrotoxic medications in CKD patients.",
    "ACOG 2023: PCOS management includes lifestyle modification, Metformin for metabolic control, and hormonal therapy for cycle regulation.",
    "ACC/AHA Post-MI: All post-MI patients should receive dual antiplatelet therapy, high-intensity statins, ACE inhibitors, and beta-blockers. Cardiac rehab enrollment within 30 days recommended.",
    "GINA 2023: Asthma control assessment includes symptom frequency, SABA use, and nighttime symptoms. Spirometry required annually.",
    "WHO Anemia: Hemoglobin <12 g/dL in women indicates anemia. Ferritin <15 ng/mL confirms iron deficiency. IV iron preferred when oral fails.",
    "Preventive Care: Annual eye exams for diabetic patients to screen for retinopathy. Annual foot exams for peripheral neuropathy.",
    "Care Coordination: High-risk patients (risk score >0.7) should have care manager assignment, monthly check-ins, and emergency care plan.",
    "Medication Adherence: Non-adherent patients should receive pharmacist consultation and automated refill reminders. Missed refills flagged within 7 days.",
    "Mental Health Integration: Screen all chronic disease patients for depression and anxiety annually using PHQ-9 and GAD-7.",
    "Appointment Adherence: Patients with 2+ missed follow-ups should receive outreach call and telehealth alternative.",
    "Social Determinants: Patients living alone with chronic disease require social work referral and community health worker support.",
    "Smoking Cessation: All smokers with cardiovascular disease must receive cessation counseling at every visit. NRT or Varenicline recommended.",
]

def _score(query: str, guideline: str) -> int:
    """Simple keyword overlap scoring — no ML needed."""
    q_words = set(re.findall(r'\w+', query.lower()))
    g_words = set(re.findall(r'\w+', guideline.lower()))
    # Remove stopwords
    stops = {'the','a','an','is','in','of','to','and','or','for','with','at','by','from','be','are','as','on','was','this'}
    q_words -= stops
    g_words -= stops
    return len(q_words & g_words)

def retrieve_guidelines(query: str, top_k: int = 3) -> list:
    scored = [(g, _score(query, g)) for g in CLINICAL_GUIDELINES]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [g for g, _ in scored[:top_k]]

def format_guidelines_for_prompt(guidelines: list) -> str:
    return '\n'.join([f'- {g}' for g in guidelines])
