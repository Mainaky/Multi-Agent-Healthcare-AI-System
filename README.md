# 🏥 CareFlow
### A Role-Based Multi-Agent AI System for Clinical Workflow Orchestration

Built to demonstrate agentic AI capabilities aligned with XCaliber Health's internship requirements.
Inspired by XCaliber's **Merlin** multi-agent architecture for care continuum automation.

---

## 🤖 What is CareFlow?

CareFlow is a multi-agent AI system where a master **Orchestrator Agent** routes clinical queries to the most appropriate specialist agent based on patient context and clinical guidelines.

| Agent | Responsibility |
|-------|---------------|
| 🗓️ **Patient Navigator** | Scheduling, refills, follow-ups, intake |
| 🔗 **Care Coordinator** | Referrals, care gap closure, task routing |
| 📊 **Quality & Risk Analyst** | Risk scoring, compliance gaps, safety flags |
| 💊 **AI Nurse** | Medication adherence, clinical prep, education |

---

## 🏗️ Project Structure
```
careflow/
├── backend/
│   ├── main.py               # FastAPI server (entry point)
│   ├── agents/
│   │   ├── orchestrator.py   # Master routing agent
│   │   ├── patient_navigator.py
│   │   ├── care_coordinator.py
│   │   ├── quality_analyst.py
│   │   └── ai_nurse.py
│   ├── tools/
│   │   ├── fhir_parser.py    # Parse synthetic FHIR data
│   │   └── rag_engine.py     # RAG over clinical guidelines
│   ├── data/
│   │   └── patients.json     # Synthetic patient data (FHIR-like)
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   └── index.html            # Single-file dashboard
├── docs/
│   └── architecture.md
└── README.md
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python |
| AI Agents | LangChain + OpenAI/Groq |
| Data | Synthetic FHIR JSON |
| RAG | Keyword-based clinical guideline retrieval |
| Frontend | Vanilla JS + CSS (no build needed) |

---

## 🚀 How to Run

### Step 1 — Clone the repo
```bash
git clone https://github.com/Mainaky/Multi-Agent-Healthcare-AI-System.git
cd Multi-Agent-Healthcare-AI-System/careflow/backend
```

### Step 2 — Create virtual environment
```bash
# Use Python 3.11 recommended
py -3.11 -m venv venv

# Activate (Windows)
.\venv\Scripts\activate
```

### Step 3 — Install dependencies
```bash
pip install fastapi uvicorn python-dotenv langchain==0.2.6 langchain-openai==0.1.13 langchain-groq==0.1.6 langchain-community==0.2.6 pydantic==2.9.2 httpx
```

### Step 4 — Get a free Groq API Key
1. Go to **https://console.groq.com**
2. Sign up → API Keys → Create Key
3. Copy the key (starts with `gsk_...`)

### Step 5 — Create .env file
```bash
# Windows PowerShell
[System.IO.File]::WriteAllText(".env", "GROQ_API_KEY=gsk_your-key-here")
```

### Step 6 — Start backend
```bash
python -W ignore -m uvicorn main:app --port 8000
```

### Step 7 — Open frontend
Open `careflow/frontend/index.html` in your browser.

---

## 📊 Evaluation Metrics

The system tracks per query:
- **Routing Accuracy** — Did orchestrator pick the right agent?
- **Response Latency** — Time to first response in ms
- **Task Completion Rate** — Was the clinical action resolved?
- **Confidence Score** — Agent's confidence in its response

View live metrics at: `http://localhost:8000/eval/summary`

---

## 🧪 Sample Queries to Try

| Patient | Query |
|---------|-------|
| Arjun Sharma | "HbA1c is 8.2, what should we do?" |
| Ramesh Gupta | "BNP is 820, assess CHF risk" |
| Priya Nair | "Patient reports increased stress" |
| Sneha Iyer | "Hemoglobin is 9.8, review iron therapy" |
| Vikram Mehta | "Patient is a smoker post-MI" |

---

## 🔗 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /patients` | All patient records |
| `GET /patients/{id}` | Single patient detail |
| `POST /query` | Submit clinical query |
| `GET /eval/summary` | Evaluation metrics |
| `GET /docs` | Interactive API docs |

---

## 🔌 Model Context Protocol (MCP) Server

CareFlow includes a native **MCP Server** (`backend/mcp_server.py`) enabling external AI agents (like Claude Desktop, Cursor, or IDE copilot) to directly invoke CareFlow clinical tools and inspect FHIR patient records via standardized JSON-RPC:

- **Resources**: `careflow://patients`, `careflow://guidelines`
- **Tools**:
  - `get_patient_profile(patient_id)`: Fetches FHIR clinical profile
  - `search_clinical_guidelines(query)`: RAG guideline retrieval
  - `triage_clinical_query(patient_id, query)`: Master Orchestrator triage
  - `execute_careflow_workflow(patient_id, query)`: End-to-end multi-agent execution

To connect with Claude Desktop or Cursor, refer to `backend/mcp_config.json`.

---

*Built by Mainak Roy — Data Science Undergraduate, NIIT University*