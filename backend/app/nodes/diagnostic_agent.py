from langchain_core.messages import HumanMessage, AIMessage
from langchain_ollama import ChatOllama
from app.state import MedicalState
from app.tools.patient_tools import DIAGNOSTIC_QUESTIONS
from app.tools.care_tools import recommend_interim_care
import os


def diagnostic_agent_node(state: MedicalState) -> MedicalState:
    question_count = state.get("question_count", 0)
    patient_answers = state.get("patient_answers", [])
    patient_case = state.get("patient_case", "")
    messages = state.get("messages", [])

    if question_count >= 5 and len(patient_answers) >= 5:
        llm = ChatOllama (
            model=os.getenv("OLLAMA_MODEL", "llama3.2:latest"),
            temperature=0.2,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )

        answers_text = "\n".join([
            f"Q{i+1}: {DIAGNOSTIC_QUESTIONS[i]}\nR: {ans}"
            for i, ans in enumerate(patient_answers[:5])
        ])

        prompt = f"""Tu es un assistant medical. Voici le cas patient et ses reponses.

Cas: {patient_case}

{answers_text}

Produis en francais une synthese clinique preliminaire courte et structuree avec:
1. Resume des symptomes
2. Orientation clinique possible
3. Points d'attention
Ne pose pas de diagnostic definitif."""

        response = llm.invoke([HumanMessage(content=prompt)])
        interim = recommend_interim_care.invoke({"symptoms_summary": patient_case})

        return {
            **state,
            "diagnostic_summary": response.content,
            "interim_care": interim,
            "messages": list(messages) + [AIMessage(content=response.content)],
            "next": "physician_review"
        }

    current_q_index = question_count
    if current_q_index < len(DIAGNOSTIC_QUESTIONS):
        current_question = DIAGNOSTIC_QUESTIONS[current_q_index]
        return {
            **state,
            "messages": list(messages) + [AIMessage(content=current_question)],
            "next": "diagnostic_agent"
        }

    return state