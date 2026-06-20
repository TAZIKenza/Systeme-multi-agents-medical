# Système Multi-Agents Médical – Orientation Clinique Préliminaire

>  **Avertissement**
>
> Ce système ne remplace en aucun cas une consultation médicale. Il fournit uniquement une **orientation clinique préliminaire** à des fins pédagogiques et de démonstration.

---

# 1. Contexte et Objectifs

Ce projet implémente un **système multi-agents médical** basé sur **LangGraph**, simulant un processus d'orientation clinique préliminaire.

Le système permet de :

*  Recueillir les informations d'un patient à travers un questionnaire successif ;
*  Générer une synthèse clinique préliminaire grâce à un agent LLM local (**LLaMA 3.2 via Ollama**) ;
*  Intégrer une validation humaine (*Human-in-the-Loop*) par un médecin ;
*  Produire un rapport clinique structuré ;
*  Exposer le système via une API REST (**FastAPI**) et une interface web (**Streamlit**) ;
*  Enrichir les analyses grâce à des outils médicaux contextuels via **MCP (Model Context Protocol)**.

---

#  2. Architecture Générale

```text
medical_multiagent/
│
├── backend/
│   ├── app/
│   │   ├── state.py
│   │   ├── graph.py
│   │   ├── nodes/
│   │   │   ├── supervisor.py
│   │   │   ├── diagnostic_agent.py
│   │   │   ├── physician_review.py
│   │   │   └── report_agent.py
│   │   ├── tools/
│   │   │   ├── patient_tools.py
│   │   │   ├── care_tools.py
│   │   │   └── mcp_client.py
│   │   └── api.py
│   │
│   ├── main.py
│   ├── langgraph.json
│   ├── requirements.txt
│   └── .env
│
├── mcp_server/
│   └── server.py
│
├── frontend/
│   └── app.py
│
└── README.md
```

---

#  3. Workflow LangGraph

## 3.1 Graphe des transitions

Le workflow est orchestré par LangGraph et intègre un mécanisme **Human-in-the-Loop (HITL)**.

```text
START
   │
   ▼
Supervisor
   │
   ▼
DiagnosticAgent
   │
   ▼
Supervisor
   │
   ▼
[INTERRUPT]
PhysicianReview
   │
   ▼
Supervisor
   │
   ▼
ReportAgent
   │
   ▼
END
```

Le graphe est compilé avec :

```python
graph = builder.compile(
    interrupt_before=["physician_review"]
)
```

---

## 3.2 Description des nœuds

| Nœud                | Rôle                  | Description                                                                                                         |
| ------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Supervisor**      | Orchestrateur         | Décide du prochain nœud selon l'état du système (`question_count`, `diagnostic_summary`, `physician_treatment`).    |
| **DiagnosticAgent** | Agent diagnostic      | Pose 5 questions au patient, génère une synthèse clinique avec LLaMA et propose des recommandations intermédiaires. |
| **PhysicianReview** | Human-in-the-Loop     | Suspend le workflow et attend la validation ou l'avis du médecin.                                                   |
| **ReportAgent**     | Générateur de rapport | Produit le rapport clinique final structuré.                                                                        |

---

## 3.3 État partagé : `MedicalState`

```python
class MedicalState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    next: Literal[...]
    question_count: int
    patient_answers: list
    interim_care: str
    diagnostic_summary: str
    physician_treatment: str
    final_report: str
    patient_case: str
```

### Description des attributs

| Attribut              | Description                         |
| --------------------- | ----------------------------------- |
| `messages`            | Historique des messages             |
| `next`                | Prochain nœud à exécuter            |
| `question_count`      | Nombre de questions posées          |
| `patient_answers`     | Réponses du patient                 |
| `interim_care`        | Recommandations intermédiaires      |
| `diagnostic_summary`  | Synthèse clinique générée           |
| `physician_treatment` | Avis du médecin                     |
| `final_report`        | Rapport clinique final              |
| `patient_case`        | Description initiale du cas patient |

---

#  4. Intégration MCP (Model Context Protocol)

Le serveur MCP fonctionne indépendamment sur le port **8001**.

Il expose plusieurs outils médicaux contextuels.

| Endpoint                          | Outil                 | Description                                                    |
| --------------------------------- | --------------------- | -------------------------------------------------------------- |
| `POST /tools/get_medical_context` | `get_medical_context` | Retourne un contexte clinique enrichi selon les symptômes.     |
| `POST /tools/check_red_flags`     | `check_red_flags`     | Détecte les signaux d'alerte médicaux (`URGENT`, `ATTENTION`). |
| `GET /tools`                      | `list_tools`          | Liste les outils disponibles.                                  |
| `GET /health`                     | `health`              | Vérifie l'état du serveur MCP.                                 |

---

#  5. API FastAPI

Le backend FastAPI est accessible sur :

```text
http://localhost:8000
```

Documentation Swagger :

```text
http://localhost:8000/docs
```

## Endpoints disponibles

| Méthode | Endpoint                           | Description                     |
| ------- | ---------------------------------- | ------------------------------- |
| `POST`  | `/sessions/start`                  | Création d'une nouvelle session |
| `POST`  | `/consultation/start`              | Démarrage de la consultation    |
| `POST`  | `/consultation/resume`             | Reprise du workflow             |
| `GET`   | `/consultation/{thread_id}`        | État courant de la consultation |
| `GET`   | `/consultation/{thread_id}/poll`   | Vérification de l'avancement    |
| `GET`   | `/consultation/{thread_id}/report` | Rapport final                   |
| `GET`   | `/health`                          | Vérification du backend         |

---

## Flux séquentiel

```text
1. POST /sessions/start
            │
            ▼
2. POST /consultation/start
            │
            ▼
3. Questions / Réponses (x5)
            │
            ▼
4. Génération de la synthèse clinique
            │
            ▼
5. Validation médecin (HITL)
            │
            ▼
6. Génération du rapport final
            │
            ▼
7. GET /report
```

---

#  6. Interface Streamlit

Le frontend est accessible sur :

```text
http://localhost:8501
```

L'application est composée de quatre écrans :

### Écran 1 — Cas patient

Saisie du motif de consultation initial.

### Écran 2 — Questions/Réponses

Affichage des cinq questions successives.

### Écran 3 — Revue médecin

Affichage de la synthèse clinique et saisie de l'avis du médecin.

### Écran 4 — Rapport final

Affichage du rapport clinique structuré.

---

#  7. Technologies Utilisées

| Technologie        | Version   | Rôle                       |
| ------------------ | --------- | -------------------------- |
| LangGraph          | >=1.2     | Orchestration multi-agents |
| LangChain          | >=1.3     | Abstraction LLM            |
| langchain-ollama   | >=1.1     | Intégration Ollama         |
| Ollama + LLaMA 3.2 | 3b/latest | Modèle local               |
| FastAPI            | >=0.111   | API REST                   |
| Streamlit          | latest    | Interface web              |
| MCP                | 1.0       | Outils contextuels         |
| Python             | 3.12      | Développement backend      |

---

#  8. Installation et Exécution

## 8.1 Prérequis

* Python 3.11+
* Git
* Ollama installé

Téléchargement du modèle :

```bash
ollama pull llama3.2
```

---

## 8.2 Installation des dépendances

### Backend

```bash
cd backend
python -m venv venv
```

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / Mac

```bash
source venv/bin/activate
```

Installation :

```bash
pip install -r requirements.txt
```

---

### MCP Server

```bash
cd ../mcp_server
pip install fastapi uvicorn httpx
```

---

### Frontend

```bash
cd ../frontend
pip install streamlit requests
```

---

## 8.3 Configuration

Créer le fichier :

```text
backend/.env
```

Contenu :

```env
OLLAMA_MODEL=llama3.2:latest
OLLAMA_BASE_URL=http://localhost:11434
```

---

# 9. Lancement du Projet

Le système nécessite **4 terminaux**.

---

## Terminal 1 — Démarrer Ollama

```bash
ollama serve
```

URL :

```text
http://localhost:11434
```

---

## Terminal 2 — Démarrer le serveur MCP

```bash
cd mcp_server
python server.py
```

ou

```bash
uvicorn server:app --reload --port 8001
```

URL :

```text
http://localhost:8001
```

Vérification :

```text
http://localhost:8001/health
```

---

## Terminal 3 — Démarrer le Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

URL :

```text
http://localhost:8000
```

Documentation :

```text
http://localhost:8000/docs
```

---

## Terminal 4 — Démarrer le Frontend

```bash
cd frontend
streamlit run app.py
```

URL :

```text
http://localhost:8501
```

---

#  10. Lancement avec LangGraph Studio

Depuis le dossier backend :

```bash
cd backend
langgraph dev
```

Le serveur LangGraph démarre sur :

```text
http://127.0.0.1:2024
```

Interface Studio :

```text
https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

---

#  Quick Start

```bash
# Terminal 1
ollama serve

# Terminal 2
cd mcp_server
python server.py

# Terminal 3
cd backend
uvicorn main:app --reload --port 8000

# Terminal 4
cd frontend
streamlit run app.py

# Optionnel
cd backend
langgraph dev
```

---

#  11. Tests et Validation

### Cas 1 — Respiratoire

```text
Patient 32 ans, toux sèche depuis 5 jours, fièvre modérée 38°C.
```

Résultat attendu :

* Orientation infection respiratoire virale.
* Recommandations symptomatiques.

---

### Cas 2 — Red Flags

```text
Patient 55 ans, douleur thoracique intense irradiant bras gauche, essoufflement.
```

Résultat attendu :

* Détection des signaux d'alerte.
* Orientation vers une prise en charge urgente.

---

### Cas 3 — Cas bénin

```text
Patient 22 ans, légers maux de tête depuis ce matin, pas de fièvre.
```

Résultat attendu :

* Conseils simples.
* Absence de red flags.

---

# Architecture d'Exécution

```text
                  ┌──────────────────┐
                  │     Ollama       │
                  │      :11434      │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ Backend FastAPI  │
                  │      :8000       │
                  └────────┬─────────┘
                           │
          ┌────────────────┴──────────────┐
          │                               │
          ▼                               ▼
┌──────────────────┐            ┌──────────────────┐
│    MCP Server    │            │ Streamlit Front  │
│      :8001       │            │      :8501       │
└──────────────────┘            └──────────────────┘

                  LangGraph Studio
                        :2024
```

---

# Projet Académique

**Master Informatique**

**Encadrant : Pr. Mohamed YOUSSFI**
