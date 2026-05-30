import streamlit as st
import requests
import json
import time

# ─── Configuration ────────────────────────────────────────────────────────────

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Orientation Clinique Preliminaire",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── Style CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background-color: #f5f3ef;
        color: #1a1a1a;
    }

    .stApp {
        background-color: #f5f3ef;
    }

    /* Header principal */
    .main-header {
        background: #1c2b3a;
        color: #f5f3ef;
        padding: 2.5rem 3rem;
        border-radius: 0 0 24px 24px;
        margin-bottom: 2.5rem;
    }

    .main-header h1 {
        font-family: 'DM Serif Display', serif;
        font-size: 2.2rem;
        font-weight: 400;
        margin: 0 0 0.4rem 0;
        letter-spacing: -0.5px;
    }

    .main-header p {
        font-size: 0.9rem;
        color: #a8b8c8;
        margin: 0;
        font-weight: 300;
    }

    /* Etapes de progression */
    .progress-bar {
        display: flex;
        gap: 0;
        margin-bottom: 2.5rem;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #ddd;
    }

    .step-indicator {
        flex: 1;
        padding: 0.85rem 1rem;
        text-align: center;
        font-size: 0.78rem;
        font-weight: 500;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        background: #fff;
        color: #888;
        border-right: 1px solid #ddd;
        transition: all 0.3s;
    }

    .step-indicator:last-child {
        border-right: none;
    }

    .step-active {
        background: #1c2b3a;
        color: #f5f3ef;
    }

    .step-done {
        background: #2d6a4f;
        color: #fff;
    }

    /* Cartes */
    .card {
        background: #ffffff;
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e8e4dc;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    }

    .card-title {
        font-family: 'DM Serif Display', serif;
        font-size: 1.3rem;
        color: #1c2b3a;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #f0ede7;
    }

    /* Question du diagnostic */
    .question-box {
        background: #1c2b3a;
        color: #f5f3ef;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        font-size: 1.05rem;
        line-height: 1.6;
        font-weight: 400;
    }

    .question-counter {
        font-size: 0.75rem;
        color: #a8b8c8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }

    /* Synthese clinique */
    .synthesis-block {
        background: #f0f7f4;
        border-left: 4px solid #2d6a4f;
        border-radius: 0 12px 12px 0;
        padding: 1.5rem;
        margin-bottom: 1rem;
        font-size: 0.95rem;
        line-height: 1.7;
        white-space: pre-wrap;
    }

    /* Avis medecin */
    .physician-block {
        background: #fef9f0;
        border-left: 4px solid #c77c08;
        border-radius: 0 12px 12px 0;
        padding: 1.5rem;
        margin-bottom: 1rem;
        font-size: 0.95rem;
        line-height: 1.7;
    }

    /* Rapport final */
    .report-block {
        background: #f8f8f8;
        border: 1px solid #e0dcd5;
        border-radius: 12px;
        padding: 2rem;
        font-size: 0.92rem;
        line-height: 1.8;
        white-space: pre-wrap;
        font-family: 'DM Mono', 'Courier New', monospace;
    }

    .disclaimer {
        background: #fff3f3;
        border: 1px solid #ffcccc;
        border-radius: 10px;
        padding: 1rem 1.5rem;
        font-size: 0.85rem;
        color: #8b0000;
        margin-top: 1.5rem;
        font-weight: 500;
    }

    /* Boutons */
    .stButton > button {
        background: #1c2b3a;
        color: #f5f3ef;
        border: none;
        border-radius: 10px;
        padding: 0.7rem 2rem;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        font-size: 0.9rem;
        letter-spacing: 0.3px;
        cursor: pointer;
        transition: background 0.2s;
        width: 100%;
    }

    .stButton > button:hover {
        background: #2d4a63;
        border: none;
    }

    /* Inputs */
    .stTextArea textarea, .stTextInput input {
        border-radius: 10px;
        border: 1.5px solid #ddd;
        font-family: 'DM Sans', sans-serif;
        font-size: 0.95rem;
        background: #fff;
    }

    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #1c2b3a;
        box-shadow: 0 0 0 2px rgba(28, 43, 58, 0.1);
    }

    /* Badge de statut */
    .status-badge {
        display: inline-block;
        padding: 0.3rem 0.9rem;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    .badge-green { background: #d4edda; color: #1a5f37; }
    .badge-blue  { background: #d1ecf1; color: #0c4a6e; }
    .badge-orange{ background: #fff3cd; color: #7d5a00; }

    /* Separateur */
    hr { border: none; border-top: 1px solid #e8e4dc; margin: 2rem 0; }

    /* Masquer elements Streamlit */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 0 !important; }

    /* Thread ID discret */
    .thread-id {
        font-size: 0.72rem;
        color: #aaa;
        font-family: monospace;
        margin-top: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)


# ─── Helpers API ──────────────────────────────────────────────────────────────

def api_start_session():
    try:
        r = requests.post(f"{API_BASE}/sessions/start", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Erreur de connexion a l'API : {e}")
        return None


def api_start_consultation(thread_id: str, patient_case: str):
    try:
        r = requests.post(
            f"{API_BASE}/consultation/start",
            json={"thread_id": thread_id, "patient_case": patient_case},
            timeout=60
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Erreur lors du demarrage : {e}")
        return None


def api_resume(thread_id: str, patient_answer=None, physician_treatment=None):
    try:
        body = {"thread_id": thread_id}
        if patient_answer is not None:
            body["patient_answer"] = patient_answer
        if physician_treatment is not None:
            body["physician_treatment"] = physician_treatment
        r = requests.post(f"{API_BASE}/consultation/resume", json=body, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Erreur lors de la reprise : {e}")
        return None


def api_poll(thread_id: str):
    try:
        r = requests.get(f"{API_BASE}/consultation/{thread_id}/poll", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None


def api_get_status(thread_id: str):
    try:
        r = requests.get(f"{API_BASE}/consultation/{thread_id}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None


def api_get_report(thread_id: str):
    try:
        r = requests.get(f"{API_BASE}/consultation/{thread_id}/report", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None


# ─── Init session state ────────────────────────────────────────────────────────

defaults = {
    "screen": "accueil",
    "thread_id": None,
    "question_number": 0,
    "current_question": None,
    "answers": [],
    "diagnostic_summary": None,
    "interim_care": None,
    "physician_treatment": None,
    "final_report": None,
    "patient_case": ""
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─── Barre de progression ──────────────────────────────────────────────────────

def render_progress(active_screen):
    steps = ["Cas patient", "Questions", "Revue medecin", "Rapport final"]
    screens = ["accueil", "questions", "medecin", "rapport"]
    
    html = '<div class="progress-bar">'
    for i, (step, screen) in enumerate(zip(steps, screens)):
        if screen == active_screen:
            css = "step-indicator step-active"
        elif screens.index(active_screen) > i:
            css = "step-indicator step-done"
        else:
            css = "step-indicator"
        html += f'<div class="{css}">{step}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ─── En-tete ─────────────────────────────────────────────────────────────────

st.markdown("""
<div class="main-header">
    <h1>Systeme d'Orientation Clinique Preliminaire</h1>
    <p>Systeme multi-agents &mdash; Usage pedagogique uniquement &mdash; Ne remplace pas une consultation medicale</p>
</div>
""", unsafe_allow_html=True)


# ─── ECRAN 1 : Saisie du cas patient ─────────────────────────────────────────

if st.session_state.screen == "accueil":
    render_progress("accueil")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Description du cas patient</div>', unsafe_allow_html=True)

        st.markdown(
            "Decrivez le motif de consultation de maniere claire et concise. "
            "Le systeme posera ensuite 5 questions pour affiner l'orientation clinique.",
            help=None
        )

        patient_case = st.text_area(
            "Cas patient",
            placeholder="Exemple : Patient de 35 ans se plaignant de douleurs thoraciques depuis 48 heures, accompagnees d'une toux seche persistante...",
            height=160,
            label_visibility="collapsed"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Demarrer la consultation"):
            if not patient_case.strip():
                st.warning("Veuillez decrire le cas patient avant de continuer.")
            else:
                with st.spinner("Initialisation de la session..."):
                    session = api_start_session()

                if session:
                    thread_id = session["thread_id"]
                    with st.spinner("Demarrage de la consultation..."):
                        result = api_start_consultation(thread_id, patient_case.strip())

                    if result:
                        st.session_state.thread_id = thread_id
                        st.session_state.patient_case = patient_case.strip()
                        st.session_state.current_question = result.get("current_question")
                        st.session_state.question_number = result.get("question_number", 1)
                        st.session_state.screen = "questions"
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Deroulement</div>', unsafe_allow_html=True)
        st.markdown("""
        <ol style="padding-left:1.2rem; line-height:2; font-size:0.9rem; color:#444;">
            <li>Saisie du cas initial</li>
            <li>5 questions diagnostiques</li>
            <li>Synthese clinique preliminaire</li>
            <li>Validation par le medecin traitant</li>
            <li>Generation du rapport final</li>
        </ol>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="disclaimer">Ce systeme ne remplace pas une consultation medicale. Il produit uniquement une orientation clinique preliminaire a but pedagogique.</div>', unsafe_allow_html=True)


# ─── ECRAN 2 : Questions / Reponses patient ───────────────────────────────────

elif st.session_state.screen == "questions":
    render_progress("questions")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Collecte des informations cliniques</div>', unsafe_allow_html=True)

        q_num = st.session_state.question_number
        question = st.session_state.current_question

        st.markdown(f"""
        <div class="question-box">
            <div class="question-counter">Question {q_num} sur 5</div>
            {question}
        </div>
        """, unsafe_allow_html=True)

        # Barre de progression des questions
        progress_val = (q_num - 1) / 5
        st.progress(progress_val)

        answer = st.text_area(
            "Reponse du patient",
            placeholder="Saisissez la reponse du patient ici...",
            height=120,
            key=f"answer_{q_num}"
        )

        if st.button("Envoyer la reponse"):
            if not answer.strip():
                st.warning("Veuillez saisir une reponse avant de continuer.")
            else:
                with st.spinner("Traitement en cours..."):
                    result = api_resume(
                        st.session_state.thread_id,
                        patient_answer=answer.strip()
                    )

                if result:
                    status = result.get("status", "")

                    if status == "en_cours":
                        st.session_state.answers.append(answer.strip())
                        st.session_state.current_question = result.get("current_question")
                        st.session_state.question_number = result.get("question_number", q_num + 1)
                        st.rerun()

                    elif status == "generating":
                        st.session_state.answers.append(answer.strip())
                        st.session_state.screen = "loading"
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Reponses enregistrees</div>', unsafe_allow_html=True)

        if st.session_state.answers:
            for i, ans in enumerate(st.session_state.answers, 1):
                st.markdown(f"""
                <div style="background:#f8f8f8; border-radius:8px; padding:0.75rem 1rem; margin-bottom:0.6rem; font-size:0.85rem;">
                    <span style="color:#888; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.5px;">Reponse {i}</span><br>
                    {ans}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#aaa; font-size:0.88rem;">Aucune reponse enregistree.</p>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="thread-id">Session : {st.session_state.thread_id}</div>', unsafe_allow_html=True)

elif st.session_state.screen == "loading":
    render_progress("questions")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Analyse en cours</div>', unsafe_allow_html=True)
    st.markdown("Le systeme analyse vos reponses et genere la synthese clinique. Cela peut prendre 1 a 2 minutes avec le modele local.", unsafe_allow_html=True)
    progress_bar = st.progress(0)
    status_text = st.empty()
    for i in range(120):
        time.sleep(2)
        progress_bar.progress(min(i / 120, 0.95))
        result = api_poll(st.session_state.thread_id)
        if result:
            s = result.get("status")
            if s == "en_attente_medecin":
                st.session_state.diagnostic_summary = result.get("diagnostic_summary")
                st.session_state.interim_care = result.get("interim_care")
                st.session_state.screen = "medecin"
                st.rerun()
            elif s == "error":
                st.error(f"Erreur : {result.get('detail')}")
                st.stop()
            else:
                status_text.markdown(f"Generation en cours...")
    st.error("Timeout - Llama3.2 prend trop de temps. Relancez.")
    st.markdown('</div>', unsafe_allow_html=True)


elif st.session_state.screen == "loading_report":
    render_progress("rapport")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Generation du rapport final</div>', unsafe_allow_html=True)
    st.markdown("Le rapport final est en cours de generation. Cela peut prendre 1 a 2 minutes.", unsafe_allow_html=True)
    progress_bar = st.progress(0)
    for i in range(300):
        time.sleep(2)
        progress_bar.progress(min(i / 120, 0.95))
        result = api_poll(st.session_state.thread_id)
        if result:
            s = result.get("status")
            if s == "rapport_genere":
                st.session_state.final_report = result.get("final_report")
                st.session_state.screen = "rapport"
                st.rerun()
            elif s == "error":
                st.error(f"Erreur : {result.get('detail')}")
                st.stop()
    st.error("Timeout - Relancez.")
    st.markdown('</div>', unsafe_allow_html=True)
# ─── ECRAN 3 : Revue medecin traitant ────────────────────────────────────────

elif st.session_state.screen == "medecin":
    render_progress("medecin")

    st.markdown("""
    <div style="background:#fff8e7; border:1px solid #f0c040; border-radius:12px; padding:1rem 1.5rem; margin-bottom:1.5rem; font-size:0.9rem; color:#7d5a00; font-weight:500;">
        Le systeme est en attente de la validation du medecin traitant.
        Veuillez examiner la synthese clinique et proposer une conduite a tenir.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Synthese clinique preliminaire</div>', unsafe_allow_html=True)

        if st.session_state.diagnostic_summary:
            st.markdown(f'<div class="synthesis-block">{st.session_state.diagnostic_summary}</div>', unsafe_allow_html=True)
        else:
            st.info("Synthese en cours de generation...")

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Recommandations intermediaires</div>', unsafe_allow_html=True)

        if st.session_state.interim_care:
            st.markdown(f'<div class="physician-block">{st.session_state.interim_care}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Avis et traitement du medecin traitant</div>', unsafe_allow_html=True)

    st.markdown(
        "En tant que medecin traitant, saisissez votre avis clinique, le traitement propose et la conduite a tenir.",
        help=None
    )

    physician_input = st.text_area(
        "Traitement et conduite a tenir",
        placeholder="Exemple : Prescription d'antibiotiques (Amoxicilline 1g x3/j pendant 7 jours), repos au domicile, controle dans 5 jours. Consultation urgente si fievre > 39.5 ou aggravation...",
        height=160,
        label_visibility="collapsed"
    )

    if st.button("Valider et generer le rapport final"):
        if not physician_input.strip():
            st.warning("Veuillez saisir votre avis medical avant de valider.")
        else:
            result = api_resume(
                st.session_state.thread_id,
                physician_treatment=physician_input.strip()
            )
            if result:
                st.session_state.physician_treatment = physician_input.strip()
                st.session_state.screen = "loading_report"
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ─── ECRAN 4 : Rapport final ──────────────────────────────────────────────────

elif st.session_state.screen == "rapport":
    render_progress("rapport")

    st.markdown("""
    <div style="background:#f0f7f4; border:1px solid #b7d9c7; border-radius:12px; padding:1rem 1.5rem; margin-bottom:1.5rem; font-size:0.9rem; color:#1a5f37; font-weight:500;">
        Consultation terminee. Le rapport d'orientation clinique preliminaire a ete genere avec succes.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Rapport d\'orientation clinique preliminaire</div>', unsafe_allow_html=True)

    if st.session_state.final_report:
        st.markdown(f'<div class="report-block">{st.session_state.final_report}</div>', unsafe_allow_html=True)
    else:
        report_data = api_get_report(st.session_state.thread_id)
        if report_data:
            st.session_state.final_report = report_data.get("final_report", "")
            st.markdown(f'<div class="report-block">{st.session_state.final_report}</div>', unsafe_allow_html=True)
        else:
            st.error("Rapport non disponible. Veuillez reessayer.")

    st.markdown('<div class="disclaimer">Ce systeme ne remplace pas une consultation medicale. Ce rapport est une orientation clinique preliminaire a but pedagogique uniquement. Tout symptome persistant ou s\'aggravant necessite une consultation medicale urgente aupres d\'un professionnel de sante qualifie.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Nouvelle consultation"):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()
