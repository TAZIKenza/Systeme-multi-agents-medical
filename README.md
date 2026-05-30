# Systeme Multi-Agents Medical — Orientation Clinique Preliminaire

**Projet academique — Master Informatique**  
**Encadrant : Pr. Mohamed YOUSSFI**  
**Technologies : LangGraph, LangChain, FastAPI, Streamlit, Ollama**


## 1. Contexte et Objectifs

Ce projet realise un systeme multi-agents base sur LangGraph simulant un
workflow d'orientation clinique preliminaire. Il permet de :

- Recueillir les informations patient via 5 questions successives
- Produire une synthese clinique preliminaire par un agent LLM
- Integrer une validation humaine par un medecin traitant (Human-in-the-Loop)
- Generer un rapport final structure


## 2. Architecture Generale
medical_multiagent/
├── backend/
│   ├── app/
│   │   ├── state.py              # Etat partage LangGraph (MedicalState)
│   │   ├── graph.py              # Construction du graphe multi-agents
│   │   ├── nodes/
│   │   │   ├── supervisor.py     # Agent orchestrateur
│   │   │   ├── diagnostic_agent.py  # Agent diagnostique
│   │   │   ├── physician_review.py  # Noeud Human-in-the-Loop
│   │   │   └── report_agent.py   # Agent generateur de rapport
│   │   ├── tools/
│   │   │   ├── patient_tools.py  # Tool : questions diagnostiques
│   │   │   ├── care_tools.py     # Tool : recommandations intermediaires
│   │   │   └── mcp_client.py     # Client MCP
│   │   └── api.py                # API FastAPI
│   ├── main.py
│   ├── langgraph.json
│   └── requirements.txt
├── mcp_server/
│   └── server.py                 # Serveur MCP avec outils medicaux
├── frontend/
│   └── app.py                    # Interface Streamlit
└── README.md


## 3. Workflow LangGraph
START
|
v
Supervisor
|
v
DiagnosticAgent  →  Tool: ask_patient_question (x5)
→  Tool: recommend_interim_care
|
v
Supervisor
|
v
PhysicianReview  ←  INTERRUPTION Human-in-the-Loop
|
v
Supervisor
|
v
ReportAgent
|
v
Supervisor
|
v
END

### Description des agents

**Supervisor** : orchestre le workflow. Decide de la prochaine etape selon
l'etat courant du graphe (question_count, diagnostic_summary, physician_treatment).

**DiagnosticAgent** : pose 5 questions successives au patient via le tool
`ask_patient_question`. Une fois les 5 reponses collectees, il invoque le LLM
pour produire une synthese clinique preliminaire et appelle `recommend_interim_care`.

**PhysicianReview** : noeud Human-in-the-Loop. Le graphe s'interrompt ici
et attend la saisie manuelle du medecin traitant via l'API ou le frontend.

**ReportAgent** : genere le rapport final structure en integrant toutes les
informations collectees : cas patient, reponses, synthese, recommandations
et avis du medecin.


## 4. Etat Partage (MedicalState)

```python
class MedicalState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    next: Literal["diagnostic_agent", "physician_review", "report_agent", "FINISH"]
    question_count: int
    patient_answers: list
    interim_care: str
    diagnostic_summary: str
    physician_treatment: str
    final_report: str
    patient_case: str
    thread_id: str
```


## 5. Intégration MCP

Le serveur MCP expose deux outils medicaux accessibles par les agents :

| Outil                 | Description                                       |
|-----------------------|---------------------------------------------------|
| `get_medical_context` | Enrichit le contexte clinique selon les symptomes |
| `check_red_flags`     | Identifie les signaux d'alerte medicaux           |

Le serveur tourne independamment sur `http://localhost:8001`.


## 6. API FastAPI

| Methode | Endpoint                          | Description                        |
|---------|-----------------------------------|------------------------------------|
| POST    | `/sessions/start`                 | Creer une session                  |
| POST    | `/consultation/start`             | Demarrer avec le cas patient       |
| POST    | `/consultation/resume`            | Envoyer reponse patient ou medecin |
| GET     | `/consultation/{thread_id}`       | Etat courant                       |
| GET     | `/consultation/{thread_id}/poll`  | Polling generation LLM             |
| GET     | `/consultation/{thread_id}/report`| Rapport final                      |

Documentation interactive : `http://localhost:8000/docs`


## 7. Frontend Streamlit

4 ecrans principaux :

- **Ecran 1** : Saisie du cas patient initial
- **Ecran 2** : Questions / Reponses successives (5 questions)
- **Ecran 3** : Revue du medecin traitant avec synthese clinique
- **Ecran 4** : Rapport final structure


## 8. Technologies Utilisees

| Technologie        | Role                                         |
|--------------------|----------------------------------------------|
| LangGraph          | Orchestration multi-agents avec etat partage |
| LangChain          | Abstraction LLM et tools                     |
| Ollama + LLaMA 3.2 | Modele LLM local (sans cle API)              |
| FastAPI            | Exposition de l'API REST                     |
| Streamlit          | Interface utilisateur                        |
| MCP                | Protocole d'integration des outils           |
| MemorySaver        | Persistance de l'etat entre les appels       |


## 9. Installation et Lancement

### Prerequis
- Python 3.11+
- Ollama installe : https://ollama.com
- Modele telecharge : `ollama pull llama3.2`

### Installation

```bash
# Backend
cd backend
pip install -r requirements.txt

# MCP Server
cd ../mcp_server
pip install fastapi uvicorn httpx

# Frontend
cd ../frontend
pip install -r requirements.txt
```

### Configuration

Creer `backend/.env` :
OLLAMA_MODEL=llama3.2:latest
OLLAMA_BASE_URL=http://localhost:11434

### Lancement (3 terminaux)

```bash
# Terminal 1
cd mcp_server && python server.py

# Terminal 2
cd backend && python main.py

# Terminal 3
cd frontend && streamlit run app.py
```

Ouvrir : `http://localhost:8501`


## 10. Jeux de Tests

### Cas 1 - Syndrome respiratoire simple
- **Cas** : Patient de 32 ans avec toux seche depuis 5 jours et fievre moderee
- **Resultat attendu** : Orientation vers infection respiratoire virale

### Cas 2 - Red flags
- **Cas** : Patient de 55 ans avec douleur thoracique intense irradiant bras gauche
- **Resultat attendu** : Signaux d'alerte detectes, consultation urgente recommandee

### Cas 3 - Cas benin
- **Cas** : Patient de 22 ans avec maux de tete depuis ce matin
- **Resultat attendu** : Recommandations simples, pas de red flags


## 11. Mention Obligatoire

**Ce systeme ne remplace pas une consultation medicale.**  
Il produit uniquement une orientation clinique preliminaire a but pedagogique.  
Tout symptome persistant necessite une consultation medicale urgente.