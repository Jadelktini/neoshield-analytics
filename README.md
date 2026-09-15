# 🛡️ NeoShield Analytics — Real-Time Credit Card Fraud Detection & Analytics Platform

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![XGBoost](https://img.shields.io/badge/XGBoost-ML-orange.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)
![Apache Superset](https://img.shields.io/badge/Apache_Superset-Docker-EE0000.svg)

**NeoShield Analytics** est une solution complète d'évaluation des risques et de détection de fraude sur les transactions par carte bancaire en temps réel. Elle combine un modèle Machine Learning prédictif (**XGBoost**), un moteur de règles d'entreprise hybride, des vérifications géographiques de vitesse physique (velocity checks), une persistance des données sur PostgreSQL et un tableau de bord analytique interactif via **Apache Superset (Docker)**.

---

## 📐 Architecture & Pipeline

```mermaid
graph TD
    A[Client / Payment Gateway] -->|HTTP POST| B[FastAPI Engine - api/main.py]
    
    subgraph Engine [Pipeline d'Évaluation]
        B --> C[Feature Engineering]
        B --> D[Business Rules Engine]
        C -->|Velocity & Features| E[XGBoost ML Model]
        D -->|Hard Rules Check| E
        E -->|Risk Score & Decision| F[Decision Engine]
    end
    
    F -->|ALLOW / FLAG / BLOCK| G[(PostgreSQL DB)]
    G -->|SQL Queries| H[Apache Superset Dashboard]

    style A fill:#2d3748,stroke:#4a5568,color:#fff
    style B fill:#1a202c,stroke:#3182ce,color:#fff
    style Engine fill:#0f172a,stroke:#334155,color:#fff
    style G fill:#1e293b,stroke:#0284c7,color:#fff
    style H fill:#1e293b,stroke:#e11d48,color:#fff


    📊 Dashboard & Monitoring (Apache Superset)
Le suivi des métriques clés de performance (KPIs) et de la fraude en temps réel est assuré par Apache Superset déployé via un conteneur Docker.

Aperçu du Dashboard
Indicateurs Visualisés :
Taux de détection de la fraude (Fraud Rate) : Suivi en temps réel de la proportion de transactions bloquées (BLOCK) vs autorisées (ALLOW).

Volume et montant des transactions : Évolution temporelle des volumes financiers traités.

Répartition géographique du risque : Cartographie des transactions par pays et catégories de marchands à haut risque (crypto, casino, etc.).

Distribution des Scores de Risque : Analyse de la répartition des scores produits par le modèle XGBoost.

✨ Fonctionnalités Clés
Scoring ML en temps réel : Inférence immédiate du risque de fraude via un modèle XGBoost entraîné sur des données de transactions par carte.

Feature Engineering dynamique : Détection automatique des comportements suspects (pays à haut risque, catégories de marchands sensibles).

Moteur de décision hybride : Combinaison de la probabilité produite par l'IA et de règles métier strictes (HIGH_RISK_COUNTRY, SUSPICIOUS_MERCHANT_CATEGORY, HIGH_AMOUNT_TRANSACTION).

Persistance PostgreSQL : Stockage automatique de chaque transaction évaluée avec son identifiant unique (TX_API_...), son score et sa décision.

Visualisation Business Intelligence : Connexion directe d'Apache Superset à la base PostgreSQL pour la génération automatique de tableaux de bord.

📁 Structure du Projet
Plaintext
neoshield_analytics/
├── api/
│   └── main.py                # Service Web FastAPI (Endpoints & Connexion DB)
├── docs/
│   └── dashboard_screenshot.png # Capture d'écran du dashboard Apache Superset
├── ml_models/
│   └── fraud_detector_model.pkl# Modèle XGBoost entraîné
├── scripts/
│   ├── train_model.py         # Script d'entraînement du modèle ML
│   └── seed_db.py             # Script d'initialisation de la base PostgreSQL
├── requirements.txt           # Dépendances Python du projet
├── .env.example               # Fichier de configuration des variables d'environnement
└── README.md                  # Documentation du projet
🛠️ Stack Technique
Langage : Python 3.10+

Framework API : FastAPI, Uvicorn, Pydantic

Machine Learning & Data : XGBoost, Scikit-Learn, Pandas, Joblib

Base de données : PostgreSQL, Psycopg2

Business Intelligence & Dashboards : Apache Superset (Docker)

Gestionnaire d'environnement : Python-dotenv

🚀 Installation & Démarrage
1. Prérequis
Python 3.10 ou supérieur

Docker et Docker Compose (pour Apache Superset)

Une instance PostgreSQL active

2. Cloner le dépôt et installer les dépendances
Bash
git clone [https://github.com/votre-utilisateur/neoshield-analytics.git](https://github.com/votre-utilisateur/neoshield-analytics.git)
cd neoshield-analytics

# Création et activation de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installation des paquets
pip install -r requirements.txt
3. Configuration des variables d'environnement
Créez un fichier .env à la racine du projet en vous basant sur .env.example :

Extrait de code
DB_HOST=localhost
DB_PORT=5432
DB_NAME=neoshield_fraud
DB_USER=analyst_user
DB_PASS=votre_mot_de_passe
4. Lancer l'API FastAPI
Bash
python3 -m uvicorn api.main:app --reload --port 8000
L'API est accessible sur http://localhost:8000. Documentation Swagger interactive disponible sur http://localhost:8000/docs.

5. Lancer Apache Superset via Docker
Afin d'accéder au tableau de bord :

Bash
docker run -d -p 8088:8088 --name superset apache/superset
Connectez-vous sur http://localhost:8088, ajoutez votre base PostgreSQL en tant que source de données et ouvrez le dashboard NeoShield.

📬 Utilisation de l'API
Endpoint : POST /api/v1/transactions/evaluate
Exemple de requête (cURL) :
Bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/transactions/evaluate' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 101,
    "card_id": 1234,
    "amount": 1250.00,
    "currency": "EUR",
    "merchant_category": "crypto",
    "merchant_country": "KY",
    "kyc_status": "verified",
    "lat": 45.5017,
    "lon": -73.5673
  }'
JSON
{
  "status": "success",
  "transaction_id": "TX_API_a1b2c3d4",
  "action": "BLOCK",
  "risk_score": 0.8924,
  "triggered_rules": [
    "HIGH_RISK_COUNTRY",
    "SUSPICIOUS_MERCHANT_CATEGORY"
  ],
  "evaluated_at": "2026-09-15T15:30:00.123456"
}
🔍 Vérification dans la Base de Données
Pour vérifier l'enregistrement des transactions évaluées par l'API :

SQL
SELECT transaction_id, card_id, amount, merchant_country, merchant_category, is_fraud, timestamp 
FROM transactions 
ORDER BY timestamp DESC 
LIMIT 5;