from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
import asyncio
import threading

from app.graph import medical_graph
from app.tools.patient_tools import DIAGNOSTIC_QUESTIONS

app = FastAPI(title="Systeme Multi-Agents Medical")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Stockage en memoire des etats de generation
generation_status = {}


class SessionResponse(BaseModel):
    thread_id: str
    message: str

class ConsultationStartRequest(BaseModel):
    thread_id: str
    patient_case: str

class ConsultationResumeRequest(BaseModel):
    thread_id: str
    patient_answer: Optional[str] = None
    physician_treatment: Optional[str] = None


def run_llm_synthesis(thread_id: str, state: dict):
    """Lance la synthese LLM dans un thread separe."""
    try:
        generation_status[thread_id] = {"status": "generating"}
        config = {"configurable": {"thread_id": thread_id}}
        events = list(medical_graph.stream(None, config=config, stream_mode="values"))
        final_state = events[-1] if events else state
        generation_status[thread_id] = {
            "status": "done",
            "diagnostic_summary": final_state.get("diagnostic_summary", ""),
            "interim_care": final_state.get("interim_care", "")
        }
    except Exception as e:
        generation_status[thread_id] = {"status": "error", "detail": str(e)}


def run_llm_report(thread_id: str):
    """Lance la generation du rapport dans un thread separe."""
    try:
        generation_status[thread_id + "_report"] = {"status": "generating"}
        config = {"configurable": {"thread_id": thread_id}}
        events = list(medical_graph.stream(None, config=config, stream_mode="values"))
        final_state = events[-1] if events else {}
        generation_status[thread_id + "_report"] = {
            "status": "done",
            "final_report": final_state.get("final_report", "")
        }
    except Exception as e:
        generation_status[thread_id + "_report"] = {"status": "error", "detail": str(e)}


@app.post("/sessions/start", response_model=SessionResponse)
async def start_session():
    thread_id = str(uuid.uuid4())
    return SessionResponse(thread_id=thread_id, message="Session creee.")


@app.post("/consultation/start")
async def start_consultation(request: ConsultationStartRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    initial_state = {
        "patient_case": request.patient_case,
        "question_count": 0,
        "patient_answers": [],
        "messages": [],
        "next": "diagnostic_agent"
    }
    try:
        medical_graph.update_state(config, initial_state)
        return {
            "thread_id": request.thread_id,
            "status": "en_cours",
            "current_question": DIAGNOSTIC_QUESTIONS[0],
            "question_number": 1,
            "total_questions": 5,
            "waiting_for": "patient_answer"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/consultation/resume")
async def resume_consultation(request: ConsultationResumeRequest):
    config = {"configurable": {"thread_id": request.thread_id}}

    try:
        current_state = medical_graph.get_state(config)
        if not current_state or not current_state.values:
            raise HTTPException(status_code=404, detail="Session introuvable.")

        state_values = current_state.values

        # Reponse medecin
        if request.physician_treatment:
            update = {
                "physician_treatment": request.physician_treatment,
                "next": "report_agent"
            }
            medical_graph.update_state(config, update)
            t = threading.Thread(
                target=run_llm_report,
                args=(request.thread_id,),
                daemon=True
            )
            t.start()
            return {
                "thread_id": request.thread_id,
                "status": "generating_report",
                "waiting_for": "poll"
            }

        # Reponse patient
        if request.patient_answer is not None:
            patient_answers = list(state_values.get("patient_answers", []))
            patient_answers.append(request.patient_answer)
            question_count = len(patient_answers)

            medical_graph.update_state(config, {
                "patient_answers": patient_answers,
                "question_count": question_count,
                "next": "diagnostic_agent"
            })

            if question_count >= 5:
                # Lancer synthese en arriere-plan
                state_snap = dict(state_values)
                state_snap["patient_answers"] = patient_answers
                state_snap["question_count"] = question_count
                t = threading.Thread(
                    target=run_llm_synthesis,
                    args=(request.thread_id, state_snap),
                    daemon=True
                )
                t.start()
                return {
                    "thread_id": request.thread_id,
                    "status": "generating",
                    "waiting_for": "poll"
                }
            else:
                return {
                    "thread_id": request.thread_id,
                    "status": "en_cours",
                    "current_question": DIAGNOSTIC_QUESTIONS[question_count],
                    "question_number": question_count + 1,
                    "total_questions": 5,
                    "waiting_for": "patient_answer"
                }

        raise HTTPException(status_code=400, detail="Fournissez patient_answer ou physician_treatment.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/consultation/{thread_id}/poll")
async def poll_generation(thread_id: str):
    """Le frontend appelle cet endpoint pour savoir si la generation est terminee."""
    # Verifier rapport
    report_key = thread_id + "_report"
    if report_key in generation_status:
        s = generation_status[report_key]
        if s["status"] == "done":
            return {"status": "rapport_genere", "final_report": s.get("final_report", "")}
        elif s["status"] == "error":
            return {"status": "error", "detail": s.get("detail", "")}
        else:
            return {"status": "generating_report"}

    # Verifier synthese
    if thread_id in generation_status:
        s = generation_status[thread_id]
        if s["status"] == "done":
            return {
                "status": "en_attente_medecin",
                "diagnostic_summary": s.get("diagnostic_summary", ""),
                "interim_care": s.get("interim_care", "")
            }
        elif s["status"] == "error":
            return {"status": "error", "detail": s.get("detail", "")}
        else:
            return {"status": "generating"}

    return {"status": "not_started"}


@app.get("/consultation/{thread_id}")
async def get_consultation_status(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    try:
        current_state = medical_graph.get_state(config)
        if not current_state or not current_state.values:
            raise HTTPException(status_code=404, detail="Session introuvable.")
        state = current_state.values
        return {
            "thread_id": thread_id,
            "status": "ok",
            "diagnostic_summary": state.get("diagnostic_summary"),
            "interim_care": state.get("interim_care"),
            "physician_treatment": state.get("physician_treatment"),
            "final_report": state.get("final_report"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/consultation/{thread_id}/report")
async def get_report(thread_id: str):
    report_key = thread_id + "_report"
    if report_key in generation_status and generation_status[report_key]["status"] == "done":
        return {"thread_id": thread_id, "final_report": generation_status[report_key].get("final_report", "")}
    raise HTTPException(status_code=404, detail="Rapport non encore disponible.")


@app.get("/health")
async def health_check():
    return {"status": "ok"}