# CareFlow — Architecture

## System Overview

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                        │
│                                                         │
│  POST /query                                            │
│       │                                                 │
│       ▼                                                 │
│  ┌──────────────┐    ┌──────────────────────────────┐  │
│  │  FHIR Parser │───▶│   Orchestrator Agent (LLM)   │  │
│  │  (patient    │    │   - Reads patient context    │  │
│  │   context)   │    │   - RAG over guidelines      │  │
│  └──────────────┘    │   - Routes to best agent     │  │
│                      └────────────┬─────────────────┘  │
│                                   │                     │
│          ┌────────────────────────┼───────────────────┐ │
│          ▼            ▼           ▼           ▼        │ │
│  ┌──────────┐ ┌───────────┐ ┌─────────┐ ┌─────────┐  │ │
│  │ Patient  │ │   Care    │ │Quality/ │ │AI Nurse │  │ │
│  │Navigator │ │Coordinator│ │  Risk   │ │         │  │ │
│  └──────────┘ └───────────┘ └─────────┘ └─────────┘  │ │
│          │                                             │ │
│          ▼                                             │ │
│  Evaluation Logger (/eval/logs, /eval/summary)         │ │
└─────────────────────────────────────────────────────────┘
    │
    ▼
Frontend Dashboard (index.html)
```

## Component Details

### Orchestrator
- Takes patient FHIR data + user query
- Retrieves top-3 relevant clinical guidelines via FAISS RAG
- Uses LLM to output routing JSON: selected_agent, reason, confidence, urgency

### Agents
Each agent receives: patient_summary (str), query (str), guidelines (list)
Returns structured JSON specific to its role

### RAG Engine
- 15 embedded clinical guidelines (ADA, AHA, KDIGO, ACOG, etc.)
- SentenceTransformer: all-MiniLM-L6-v2
- FAISS IndexFlatIP (cosine similarity)
- Returns top-3 most relevant guidelines per query

### Evaluation
Logs per query:
- selected_agent
- routing confidence
- latency_ms
- task_completion status

## Data Flow
1. Frontend sends POST /query {patient_id, query}
2. Backend fetches patient from patients.json
3. Orchestrator routes to agent
4. Agent runs with patient context + guidelines
5. Response + eval metrics returned to frontend
