"""
Serveur MCP (Model Context Protocol) - Outils medicaux contextuels
Expose des outils d'enrichissement du contexte medical pour les agents LangGraph.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(
    title="MCP Medical Server",
    description="Serveur MCP exposant des outils medicaux contextuels",
    version="1.0.0"
)


# ─── Schemas ─────────────────────────────────────────────────────────────────

class SymptomsInput(BaseModel):
    symptoms: str


class MedicalContextResponse(BaseModel):
    context: str
    sources: List[str]


class RedFlagsResponse(BaseModel):
    red_flags: List[str]
    severity: str


# ─── Base de connaissances locale ─────────────────────────────────────────────

RED_FLAGS_KEYWORDS = {
    "douleur thoracique": "URGENT - Douleur thoracique pouvant indiquer une pathologie cardiaque.",
    "essoufflement severe": "URGENT - Dyspnee severe necessitant une evaluation immediate.",
    "perte de connaissance": "URGENT - Syncope ou lipothymie, evaluation medicale immediate requise.",
    "paralysie": "URGENT - Deficit neurologique, consultation neurologique urgente.",
    "sang": "ATTENTION - Presence de sang, surveillance rapprochee necessaire.",
    "fievre elevee": "ATTENTION - Hyperthermie importante, risque infectieux a evaluer.",
    "confusion": "URGENT - Etat confusionnel, evaluation neurologique urgente.",
    "vomissement sang": "URGENT - Hematemese, prise en charge urgente requise.",
    "douleur abdominale intense": "ATTENTION - Douleur abdominale intense, diagnostic differentiel urgent."
}

MEDICAL_CONTEXTS = {
    "respiratoire": """Contexte clinique respiratoire :
- Evaluer la frequence respiratoire (normale : 12-20/min adulte)
- Rechercher signes de detresse respiratoire : tirage, cyanose, SpO2
- Antecedents asthme, BPCO, tabagisme a considerer
- Eliminer une pneumopathie infectieuse, embolie pulmonaire""",

    "digestif": """Contexte clinique digestif :
- Caracteriser la douleur : siege, irradiation, type, intensite
- Rechercher signes associes : nausees, vomissements, transit
- Evaluer l'hydratation et l'etat general
- Antecedents chirurgicaux abdominaux importants""",

    "general": """Contexte clinique general :
- Evaluer l'etat general : asthenie, amaigrissement, fievre
- Rechercher des signes infectieux ou inflammatoires
- Antecedents medicaux, traitements en cours, allergies
- Contexte epidemiologique et social"""
}


# ─── Endpoints MCP ───────────────────────────────────────────────────────────

@app.post("/tools/get_medical_context", response_model=MedicalContextResponse)
async def get_medical_context(input: SymptomsInput):
    """
    Retourne un contexte medical enrichi selon les symptomes decrits.
    """
    symptoms_lower = input.symptoms.lower()
    context = ""

    if any(word in symptoms_lower for word in ["toux", "respir", "essouffl", "poumon", "bronch"]):
        context = MEDICAL_CONTEXTS["respiratoire"]
    elif any(word in symptoms_lower for word in ["ventre", "abdom", "nausee", "vomiss", "diarrh"]):
        context = MEDICAL_CONTEXTS["digestif"]
    else:
        context = MEDICAL_CONTEXTS["general"]

    return MedicalContextResponse(
        context=context,
        sources=["Base MCP locale - Usage pedagogique uniquement"]
    )


@app.post("/tools/check_red_flags", response_model=RedFlagsResponse)
async def check_red_flags(input: SymptomsInput):
    """
    Identifie les signaux d'alerte (red flags) dans la description des symptomes.
    """
    symptoms_lower = input.symptoms.lower()
    detected_flags = []
    severity = "normal"

    for keyword, flag_message in RED_FLAGS_KEYWORDS.items():
        if any(word in symptoms_lower for word in keyword.split()):
            detected_flags.append(flag_message)
            if "URGENT" in flag_message:
                severity = "urgent"
            elif severity != "urgent" and "ATTENTION" in flag_message:
                severity = "attention"

    return RedFlagsResponse(
        red_flags=detected_flags if detected_flags else ["Aucun signal d'alerte majeur detecte."],
        severity=severity
    )


@app.get("/tools")
async def list_tools():
    """Liste les outils MCP disponibles."""
    return {
        "tools": [
            {
                "name": "get_medical_context",
                "description": "Enrichit le contexte clinique selon les symptomes",
                "input_schema": {"symptoms": "string"}
            },
            {
                "name": "check_red_flags",
                "description": "Identifie les signaux d'alerte medicaux",
                "input_schema": {"symptoms": "string"}
            }
        ]
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MCP Medical Server"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)
