"""
CareFlow MCP (Model Context Protocol) Server
Exposes CareFlow's clinical multi-agent orchestrator, synthetic FHIR records,
and RAG clinical guidelines as standardized MCP Tools and Resources.

Compatible with any MCP Host (Claude Desktop, Cursor, Antigravity IDE, etc.).
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))

from mcp.server.mcpserver import MCPServer
from tools.fhir_parser import get_all_patient_summaries, get_patient_by_id, build_patient_summary
from tools.rag_engine import retrieve_guidelines, CLINICAL_GUIDELINES
from agents.orchestrator import route_query
import agents.patient_navigator as patient_navigator
import agents.care_coordinator as care_coordinator
import agents.quality_analyst as quality_analyst
import agents.ai_nurse as ai_nurse

# Initialize the MCP Server
mcp = MCPServer(
    name="CareFlow-Clinical-Orchestrator",
    version="1.0.0"
)

AGENT_MAP = {
    "patient_navigator": patient_navigator.run,
    "care_coordinator": care_coordinator.run,
    "quality_analyst": quality_analyst.run,
    "ai_nurse": ai_nurse.run,
}

# ============================================================================
# MCP RESOURCES (Read-only clinical context)
# ============================================================================

@mcp.resource("careflow://patients")
def get_patients_resource() -> str:
    """Provides read-only access to all synthetic FHIR patient summaries in CareFlow."""
    return json.dumps(get_all_patient_summaries(), indent=2)

@mcp.resource("careflow://guidelines")
def get_guidelines_resource() -> str:
    """Provides read-only access to all 15 embedded evidence-based clinical guidelines (ADA, AHA, KDIGO, etc.)."""
    return json.dumps(CLINICAL_GUIDELINES, indent=2)

# ============================================================================
# MCP TOOLS (Executable clinical workflows)
# ============================================================================

@mcp.tool()
def get_patient_profile(patient_id: str) -> dict:
    """
    Retrieves the complete FHIR clinical profile, vitals, biomarkers,
    and active care gaps for a specific patient.
    
    Args:
        patient_id: The unique identifier (e.g., 'P001', 'P002', 'P003', 'P004', 'P005').
    """
    patient = get_patient_by_id(patient_id)
    if not patient:
        return {"error": f"Patient {patient_id} not found."}
    return patient

@mcp.tool()
def search_clinical_guidelines(query: str, top_k: int = 3) -> list[str]:
    """
    Performs RAG retrieval across 15 evidence-based clinical guidelines
    (ADA 2024, AHA 2023, KDIGO 2022, ACC/AHA, GINA, WHO) for a given clinical query.
    
    Args:
        query: Medical condition, lab result, or question (e.g. 'HbA1c 8.2', 'BNP elevated', 'eGFR declining').
        top_k: Number of guidelines to return (default: 3).
    """
    return retrieve_guidelines(query, top_k=top_k)

@mcp.tool()
def triage_clinical_query(patient_id: str, query: str) -> dict:
    """
    Invokes CareFlow's Master Orchestrator Agent to perform autonomous clinical
    triage, assessing urgency (low, medium, high, critical), routing confidence,
    and delegating to the appropriate specialist agent.
    
    Args:
        patient_id: Patient ID (e.g. 'P001').
        query: Clinical inquiry or scenario (e.g. 'HbA1c is uncontrolled at 8.2, what should we do?').
    """
    return route_query(patient_id, query)

@mcp.tool()
def execute_careflow_workflow(patient_id: str, query: str) -> dict:
    """
    Executes the full end-to-end multi-agent clinical workflow:
    1. Loads patient FHIR context.
    2. Retrieves matching guidelines via RAG.
    3. Runs Orchestrator triage.
    4. Invokes the selected specialist agent (Patient Navigator, Care Coordinator, Quality Analyst, or AI Nurse).
    5. Returns structured clinical recommendations with evaluation telemetry.
    
    Args:
        patient_id: Patient ID (e.g., 'P001', 'P003').
        query: The clinical scenario to resolve.
    """
    routing_result = route_query(patient_id, query)
    routing = routing_result["routing"]
    selected_agent = routing.get("selected_agent", "care_coordinator")
    
    agent_fn = AGENT_MAP.get(selected_agent, care_coordinator.run)
    agent_response = agent_fn(
        routing_result["patient_summary"],
        query,
        routing_result["guidelines_used"]
    )
    
    return {
        "status": "success",
        "orchestrator_decision": routing,
        "specialist_agent": selected_agent,
        "agent_response": agent_response,
        "guidelines_used": routing_result["guidelines_used"],
        "patient": routing_result["patient"]
    }

# ============================================================================
# MCP PROMPTS (Reusable Clinical Prompt Templates)
# ============================================================================

@mcp.prompt("clinical_triage_prompt")
def clinical_triage_prompt(patient_id: str, scenario: str) -> str:
    """Standardized prompt template for clinical triage evaluation."""
    patient = get_patient_by_id(patient_id)
    summary = build_patient_summary(patient)
    return (
        f"You are a clinical decision-support agent reviewing the following patient case:\n"
        f"Context: {summary}\n"
        f"Scenario: {scenario}\n\n"
        f"Evaluate clinical urgency, assess relevant guidelines, and determine next clinical actions."
    )

if __name__ == "__main__":
    # Runs the standard stdio MCP transport
    mcp.run()
