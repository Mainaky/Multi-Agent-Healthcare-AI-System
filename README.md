# 🏥 CareFlow
### A Role-Based Multi-Agent AI System for Clinical Workflow Orchestration

Built to demonstrate agentic AI capabilities aligned with XCaliber Health's internship requirements.

---

## 📁 Project Structure

```
careflow/
├── backend/
│   ├── main.py              # FastAPI server (entry point)
│   ├── agents/
│   │   ├── orchestrator.py  # Master routing agent
│   │   ├── patient_navigator.py
│   │   ├── care_coordinator.py
│   │   ├── quality_analyst.py
│   │   └── ai_nurse.py
│   ├── tools/
│   │   ├── fhir_parser.py   # Parse synthetic FHIR data
│   │   └── rag_engine.py    # RAG over clinical guidelines
│   ├── data/
│   │   └── patients.json    # Synthetic patient data (FHIR-like)
│   └── requirements.txt
├── frontend/
│   ├── index.html           # Single-file React app (CDN)
│   └── styles.css
├── docs/
│   └── architecture.md
└── README.md
```

---

## ⚙️ Prerequisites

Make sure these are installed on your machine:

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.10+ | https://python.org |
| pip | latest | comes with Python |
| Node.js (optional) | 18+ | https://nodejs.org |

---

## 🚀 Setup Instructions (Step by Step)

### Step 1 — Get an OpenAI or Groq API Key

**Option A: OpenAI (recommended)**
1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-...`)

**Option B: Groq (free & fast)**
1. Go to https://console.groq.com
2. Sign up and go to API Keys
3. Create a new key

---

### Step 2 — Setup the Backend

Open your terminal and run these commands:

```bash
# Navigate to backend folder
cd careflow/backend

# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### Step 3 — Set Your API Key

Create a `.env` file inside the `backend/` folder:

```
# careflow/backend/.env

# Paste your key here (choose one):
OPENAI_API_KEY=sk-your-key-here

# OR if using Groq:
GROQ_API_KEY=gsk_your-key-here
```

> ⚠️ Never share this file or push it to GitHub!

---

### Step 4 — Run the Backend Server

```bash
# Make sure you're in careflow/backend/ with venv active
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Test it by opening: http://localhost:8000/docs

---

### Step 5 — Open the Frontend

1. Open a **new terminal** (keep backend running)
2. Navigate to `careflow/frontend/`
3. Open `index.html` directly in your browser

**OR** serve it with Python:
```bash
cd careflow/frontend
python -m http.server 3000
# Then open http://localhost:3000
```

---

## 🧪 How to Use CareFlow

1. The dashboard shows 5 AI agents (like XCaliber's Merlin)
2. Select a patient from the left panel
3. Type a clinical query (e.g., "Patient missed 2 follow-ups, needs rescheduling")
4. The **Orchestrator Agent** decides which specialist agent to route to
5. The chosen agent responds with a structured care action
6. See reasoning, confidence score, and recommended next steps

---

## 🤖 Agent Roles

| Agent | Responsibility |
|-------|---------------|
| **Orchestrator** | Routes queries to the right specialist agent |
| **Patient Navigator** | Scheduling, refills, follow-ups, intake |
| **Care Coordinator** | Cross-team task routing, gap closure |
| **Quality & Risk Analyst** | Flags compliance gaps, risk scoring |
| **AI Nurse** | Medication adherence, clinical prep |

---

## 📊 Evaluation Metrics

The system logs:
- **Routing Accuracy** — Did the orchestrator pick the right agent?
- **Response Latency** — Time to first token
- **Hallucination Risk Score** — Based on source grounding
- **Task Completion Rate** — Was the clinical action resolved?

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python |
| AI Agents | LangChain + OpenAI/Groq |
| Data | Synthetic FHIR JSON |
| RAG | FAISS + sentence-transformers |
| Frontend | Vanilla JS + CSS (no build needed) |

---

## 🐛 Troubleshooting

**"ModuleNotFoundError"** → Make sure venv is activated and you ran `pip install -r requirements.txt`

**"Invalid API Key"** → Double-check your `.env` file has no spaces around `=`

**CORS error in browser** → Make sure backend is running on port 8000

**Port already in use** → Run `uvicorn main:app --reload --port 8001`

---

## 📝 Project Credits

Built as an internship project demonstration for XCaliber Health Pvt. Limited.
Inspired by the Merlin multi-agent architecture for care continuum automation.
