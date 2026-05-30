from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_ollama import ChatOllama
from app.state import MedicalState
from datetime import datetime
import os

REPORT_SYSTEM = """Tu es un assistant specialise dans la redaction de rapports cliniques preliminaires.
Tu produis des rapports structures, clairs et professionnels en francais.
Le rapport doit etre factuel, base uniquement sur les informations collectees.
Il ne s'agit pas d'un document medical officiel mais d'une orientation clinique preliminaire."""


def report_agent_node(state: MedicalState) -> MedicalState:
    """
    Agent de rapport : genere le rapport final structure apres validation du medecin.
    """
    llm = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "llama3.2:latest"),
    temperature=0.1,
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )

    patient_case = state.get("patient_case", "Non renseigne")
    diagnostic_summary = state.get("diagnostic_summary", "Non disponible")
    interim_care = state.get("interim_care", "Non disponible")
    physician_treatment = state.get("physician_treatment", "Non renseigne")
    patient_answers = state.get("patient_answers", [])
    messages = state.get("messages", [])

    from app.tools.patient_tools import DIAGNOSTIC_QUESTIONS
    qa_section = ""
    for i, ans in enumerate(patient_answers[:5]):
        if i < len(DIAGNOSTIC_QUESTIONS):
            qa_section += f"\nQuestion {i+1} : {DIAGNOSTIC_QUESTIONS[i]}\nReponse : {ans}\n"

    report_prompt = f"""Genere un rapport clinique preliminaire complet et structure avec les sections suivantes :

---
RAPPORT D'ORIENTATION CLINIQUE PRELIMINAIRE
Date : {datetime.now().strftime('%d/%m/%Y a %H:%M')}
---

1. MOTIF DE CONSULTATION
{patient_case}

2. ANAMNESE - REPONSES DU PATIENT
{qa_section if qa_section else "Non disponible"}

3. SYNTHESE CLINIQUE PRELIMINAIRE
{diagnostic_summary}

4. RECOMMANDATIONS INTERMEDIAIRES DE PRECAUTION
{interim_care}

5. AVIS ET TRAITEMENT DU MEDECIN TRAITANT
{physician_treatment}

6. CONCLUSION ET SUIVI RECOMMANDE
Redige une conclusion synthétique et les étapes de suivi recommandées.

---
MENTION OBLIGATOIRE :
Ce systeme ne remplace pas une consultation medicale. Ce rapport est une orientation clinique preliminaire a but pedagogique uniquement. Tout symptome persistant ou s'aggravant necessite une consultation medicale urgente.
---

Produis ce rapport de maniere professionnelle et lisible."""

    response = llm.invoke([
        SystemMessage(content=REPORT_SYSTEM),
        HumanMessage(content=report_prompt)
    ])

    new_messages = list(messages) + [
        AIMessage(content="Rapport final genere avec succes.")
    ]

    return {
        **state,
        "final_report": response.content,
        "messages": new_messages,
        "next": "FINISH"
    }
