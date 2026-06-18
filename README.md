# Système Multi-Agents Médical – Orientation Clinique Préliminaire

> ⚠️ **Mention obligatoire**  
Ce système ne remplace pas une consultation médicale. Il fournit uniquement une orientation clinique préliminaire.


## 1. Contexte et Objectifs

Ce projet réalise un système multi-agents basé sur **LangGraph**, simulant un workflow d’orientation clinique préliminaire. Il permet de :

- 📥 Recueillir les informations patient via un questionnaire successif  
- 🧠 Produire une synthèse clinique préliminaire via un agent LLM local (Ollama)  
- 👨‍⚕️ Intégrer une validation humaine par un médecin (Human-in-the-Loop)  
- 📄 Générer un rapport final structuré  
- 🚀 Exposer le système via une API FastAPI + interface Streamlit  
- 🔌 Intégrer des outils médicaux contextuels via MCP (Model Context Protocol)


## 2. Architecture Générale

```text
medical_multiagent/
│── backend/
│   │── app/
│   │   ├── state.py
│   │   ├── graph.py
│   │   ├── nodes/
│   │   ├── tools/
│   │   ├── api.py
│   │── main.py
│   │── langgraph.json
│   │── requirements.txt
│
│── mcp_server/
│── frontend/
│── README.md

```


## 3. Workflow LangGraph

### 3.1 Graphe des transitions

Le graphe est défini dans `graph.py` et compilé avec `interrupt_before=["physician_review"]` pour implémenter le mécanisme *Human-in-the-Loop* :

```text
START ➔ Supervisor ➔ DiagnosticAgent ➔ Supervisor ➔ [INTERRUPT] PhysicianReview ➔ Supervisor ➔ ReportAgent ➔ END

```

### 3.2 Description des nœuds

| Nœud                | Rôle              | Détails                                                                                  |
|---------------------|-------------------|------------------------------------------------------------------------------------------|
| **Supervisor**      | Orchestrateur     | Décide du prochain nœud selon l'état courant (`question_count`, `diagnostic_summary` `physician_treatment`).                                                                                                              |
| **DiagnosticAgent** | Agent diagnostic  | Pose 5 questions via `ask_patient_question`. Génère la synthèse clinique avec ChatOllama (`llama3.2`) et appelle `recommend_interim_care`.                                                                                    |
| **PhysicianReview** | Human-in-the-Loop | Interruption du graphe. Attend la saisie manuelle du médecin via l'API ou LangGraph Studio avant de continuer.                                                                                                                  |
| **ReportAgent**     | Rédaction rapport | Génère le rapport final structuré en 6 sections intégrant toutes les données collectées. |

### 3.3 État partagé — `MedicalState`

L'état est défini dans `state.py` et partagé entre tous les nœuds :

```python
class MedicalState(TypedDict, total=False):
    messages: Annotated[list, add_messages]   # Historique des messages
    next: Literal[...]                        # Prochain nœud
    question_count: int                       # Nb questions posées (0-5)
    patient_answers: list                     # Réponses du patient
    interim_care: str                         # Recommandations intermédiaires
    diagnostic_summary: str                   # Synthèse clinique LLM
    physician_treatment: str                  # Avis du médecin traitant
    final_report: str                         # Rapport final
    patient_case: str                         # Cas patient initial

```

### 3.4 Compilation du graphe

Le graphe est compilé sans checkpointer personnalisé — LangGraph Studio gère la persistance automatiquement :

```python
graph = builder.compile(interrupt_before=["physician_review"])

```

### 3.5 Configuration LangGraph Studio — `langgraph.json`

```json
{
  "dependencies": ["."],
  "graphs": {
    "medical_graph": "./app/graph.py:medical_graph"
  },
  "env": ".env"
}

```

---

## 4. Intégration MCP (Model Context Protocol)

Le serveur MCP tourne indépendamment sur le port `8001` et expose deux outils médicaux contextuels appelés par le client via HTTP :

| Endpoint                          | Outil                 | Description                            |
|-----------------------------------|-----------------------|----------------------------------------|
| `POST /tools/get_medical_context` | `get_medical_context` | Retourne un contexte clinique enrichi selon les symptômes (respiratoire, digestif, général).                                                                                  |
| `POST /tools/check_red_flags`     | `check_red_flags`     | Détecte les signaux d'alerte médicaux (`URGENT` / `ATTENTION`) dans la description.                                                                                         |
| `GET /tools`                      | `list_tools`          | Liste tous les outils MCP disponibles. |
| `GET /health`                     | `health`              | Vérification de l'état du serveur MCP. |

---

## 5. API FastAPI

Le backend FastAPI tourne sur le port `8000`. La documentation interactive Swagger est accessible sur : `http://localhost:8000/docs`.

### Endpoints disponibles

| Méthode| Endpoint                           | Description                                                                             |
|--------|------------------------------------|-----------------------------------------------------------------------------------------|
| `POST` | `/sessions/start`                  | Crée une nouvelle session (génère un `thread_id` UUID).                                 |
| `POST` | `/consultation/start`              | Démarre la consultation avec le cas patient initial.                                    |
| `POST` | `/consultation/resume`             | Envoie la réponse patient (`patient_answer`) ou l'avis médecin (`physician_treatment`). |
| `GET`  | `/consultation/{thread_id}`        | Retourne l'état courant de la consultation.                                             |
| `GET`  | `/consultation/{thread_id}/poll`   | Polling — vérifie si la génération LLM est terminée.                                    |
| `GET`  | `/consultation/{thread_id}/report` | Retourne le rapport final une fois généré.                                              |
| `GET`  | `/health`                          | Vérification de l'état du backend.                                                      |

### Flux séquentiel complet

1. `POST /sessions/start` ➔ Obtenir le `thread_id`
2. `POST /consultation/start {thread_id, patient_case}` ➔ Récupérer la première question
3. `POST /consultation/resume {thread_id, patient_answer}` **(× 5)** ➔ Questions/Réponses successives
4. `GET /consultation/{thread_id}/poll` ➔ Attendre la fin de la génération de la synthèse LLM
5. `POST /consultation/resume {thread_id, physician_treatment}` ➔ Soumettre l'avis du médecin
6. `GET /consultation/{thread_id}/poll` ➔ Attendre la génération du rapport final
7. `GET /consultation/{thread_id}/report` ➔ Récupérer le rapport final complet

---

## 6. Frontend Streamlit

L'interface tourne sur le port `8501` et se décompose en 4 écrans :

* **Écran 1 — Cas patient :** Saisie du motif de consultation initial.
* **Écran 2 — Q/R patient :** Affichage des 5 questions successives et saisie des réponses.
* **Écran 3 — Revue médecin :** Affichage de la synthèse clinique et saisie de l'avis médecin (HITL).
* **Écran 4 — Rapport final :** Affichage du rapport clinique structuré complet.

---

## 7. Technologies Utilisées

| Technologie            | Version     | Rôle                                                |
|------------------------|-------------|-----------------------------------------------------|
| **LangGraph**          | `>=1.2`     | Orchestration multi-agents, gestion de l'état, HITL |
| **LangChain**          | `>=1.3`     | Abstraction LLM et outils                           |
| **langchain-ollama**   | `>=1.1`     | Intégration Ollama/LLaMA local                      |
| **Ollama + LLaMA 3.2** | `3b/latest` | Modèle LLM local (sans clé API, nécessite ~8GB RAM) |
| **FastAPI**            | `>=0.111`   | Exposition de l'API REST                            |
| **Streamlit**          | `latest`    | Interface utilisateur web                           |
| **MCP (FastAPI)**      | `1.0`       | Serveur d'outils médicaux contextuels               |
| **Python**             | `3.12`      | Langage de programmation backend                    |

---

## 8. Installation et Lancement

### 8.1 Prérequis

* Python `3.11+`
* **Ollama** installé ([Télécharger ici](https://ollama.com))
* Modèle local téléchargé : `ollama pull llama3.2`

### 8.2 Installation des dépendances

Ouvrez vos terminaux et exécutez les commandes suivantes selon les dossiers :

```bash
# 1. Dans le dossier Backend
cd backend
pip install -r requirements.txt

# 2. Dans le dossier MCP Server
cd ../mcp_server
pip install fastapi uvicorn httpx

# 3. Dans le dossier Frontend
cd ../frontend
pip install streamlit requests

```

### 8.3 Configuration de l'environnement

Créez un fichier `.env` dans le dossier `backend/` :

```env
OLLAMA_MODEL=llama3.2:latest
OLLAMA_BASE_URL=http://localhost:11434

```

### 8.4 Lancement du projet complet (3 Terminaux)

| Terminal       | Commande                                              | URL d'accès             |
|----------------|-------------------------------------------------------|-------------------------|
| **Terminal 1** | `cd mcp_server && python server.py`                   | `http://localhost:8001` |
| **Terminal 2** | `cd backend && uvicorn main:app --reload --port 8000` | `http://localhost:8000` |
| **Terminal 3** | `cd frontend && streamlit run app.py`                 | `http://localhost:8501` |

*Note : Assurez-vous qu'Ollama tourne bien en arrière-plan avec la commande `ollama serve`.*

### 8.5 Lancement de la Démo sur LangGraph Studio

```bash
cd backend
langgraph dev

```

Ouvrir ensuite l'interface via l'URL : [LangGraph Studio](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024)

---

## 9. Tests et Validation (LangGraph Studio)

### 9.1 Input Initial du Graphe

Dans le panneau **Input** de LangGraph Studio, injecter la structure suivante :

```json
{
  "patient_case": "<description du cas>",
  "question_count": 0,
  "patient_answers": [],
  "messages": [],
  "next": "diagnostic_agent"
}

```

### 9.2 Gestion de l'interruption HITL

Le graphe s'arrête automatiquement sur le nœud `physician_review`. Dans le panneau **State** :

1. Cliquez sur **Edit**.
2. Ajoutez votre avis médical :
```json
{
  "physician_treatment": "<traitement proposé>"
}

```


3. Cliquez sur **Continue** pour relancer le workflow et générer le rapport.

### 9.3 Jeux de tests types

| Cas | `patient_case` (Input) | Résultat attendu | `physician_treatment` (Exemple) |
| --- | --- | --- | --- |
| **1 — Respiratoire** | "Patient 32 ans, toux sèche depuis 5 jours, fièvre modérée 38°C" | Orientation infection respiratoire virale | "Paracétamol 1g/8h, repos 3 jours" |
| **2 — Red flags** | "Patient 55 ans, douleur thoracique intense irradiant bras gauche, essoufflement" | Signaux d'alerte, orientation consultation urgente | "Orientation urgences cardiologiques, ECG immédiat" |
| **3 — Bénin** | "Patient 22 ans, légers maux de tête depuis ce matin, pas de fièvre" | Recommandations simples, pas de red flags | "Paracétamol si besoin, hydratation, repos" |

### 9.4 Éléments clés pour la validation (Évaluation)

Lors de la présentation, les points suivants doivent être visibles dans LangGraph Studio :

* Les transitions dynamiques entre les nœuds gérées par le `Supervisor`.
* L'interruption automatique (*Human-in-the-Loop*) au niveau du nœud `physician_review`.
* La mise à jour en temps réel des états intermédiaires (`diagnostic_summary`, `interim_care`, etc.).
* La reprise fluide du graphe après l'injection des données du médecin pour aboutir au rapport final.

---

**Projet académique — Master Informatique** | Encadrant : **Pr. Mohamed YOUSSFI**

```

```
