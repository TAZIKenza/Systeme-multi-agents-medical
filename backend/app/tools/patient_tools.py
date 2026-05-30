from langchain_core.tools import tool
from typing import Optional


DIAGNOSTIC_QUESTIONS = [
    "Depuis combien de temps ressentez-vous ces symptomes ?",
    "Pouvez-vous decrire la nature et l'intensite de la douleur ou de l'inconfort (sur 10) ?",
    "Avez-vous de la fievre, des frissons ou des sueurs nocturnes ?",
    "Avez-vous des antecedents medicaux, des allergies ou prenez-vous des medicaments en cours ?",
    "Avez-vous remarque d'autres symptomes associes (nausees, vomissements, essoufflement, etc.) ?"
]


@tool
def ask_patient_question(question_index: int) -> str:
    """
    Retourne la question diagnostique correspondant a l'index fourni (0 a 4).
    Utiliser successivement pour collecter les informations patient.
    """
    if 0 <= question_index < len(DIAGNOSTIC_QUESTIONS):
        return DIAGNOSTIC_QUESTIONS[question_index]
    return "Toutes les questions ont ete posees."


@tool
def get_all_questions() -> list:
    """Retourne la liste complete des 5 questions diagnostiques."""
    return DIAGNOSTIC_QUESTIONS
