from langchain_core.messages import AIMessage, HumanMessage
from app.state import MedicalState


def physician_review_node(state: MedicalState) -> MedicalState:
    """
    Noeud Human-in-the-Loop representant le medecin traitant.
    Ce noeud est interrompu par LangGraph via interrupt() pour attendre
    la saisie manuelle du medecin avant de continuer.
    """
    # Ce noeud est interrompu automatiquement par le mecanisme interrupt_before
    # de LangGraph Studio et de l'API. Le medecin saisit son traitement via
    # POST /consultation/resume avec physician_treatment dans le body.
    
    diagnostic_summary = state.get("diagnostic_summary", "")
    interim_care = state.get("interim_care", "")
    physician_treatment = state.get("physician_treatment", "")
    messages = state.get("messages", [])

    if physician_treatment:
        new_messages = list(messages) + [
            AIMessage(content=f"Avis du medecin traitant enregistre : {physician_treatment}")
        ]
        return {
            **state,
            "messages": new_messages,
            "next": "report_agent"
        }

    # Etat d'attente : pas encore de reponse medecin
    return {
        **state,
        "next": "physician_review"
    }
