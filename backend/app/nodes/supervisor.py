from langchain_core.messages import SystemMessage, HumanMessage
from app.state import MedicalState
import os


def supervisor_node(state: MedicalState) -> MedicalState:
    """
    Le Supervisor orchestre le workflow medical.
    Il decide de la prochaine etape selon l'etat courant.
    """
    question_count = state.get("question_count", 0)
    diagnostic_summary = state.get("diagnostic_summary", "")
    physician_treatment = state.get("physician_treatment", "")
    final_report = state.get("final_report", "")
    next_step = state.get("next", None)

    # Logique de routage
    if next_step == "FINISH" or final_report:
        return {**state, "next": "FINISH"}

    if physician_treatment and not final_report:
        return {**state, "next": "report_agent"}

    if diagnostic_summary and not physician_treatment:
        return {**state, "next": "physician_review"}

    if question_count < 5:
        return {**state, "next": "diagnostic_agent"}

    if question_count >= 5 and not diagnostic_summary:
        return {**state, "next": "diagnostic_agent"}

    return {**state, "next": "diagnostic_agent"}


def route_supervisor(state: MedicalState) -> str:
    """Fonction de routage conditionnelle depuis le supervisor."""
    return state.get("next", "diagnostic_agent")
