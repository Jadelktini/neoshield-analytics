import os
import sys
import uuid
from pathlib import Path
from datetime import datetime
import joblib
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

app = FastAPI(
    title="NeoShield Analytics - Fraud Detection API",
    version="1.0.0"
)

# Chargement du modèle XGBoost
MODEL_PATH = Path("ml_models/fraud_detector_model.pkl")

if MODEL_PATH.exists():
    model = joblib.load(MODEL_PATH)
else:
    model = None

# Variables de connexion PostgreSQL (depuis .env avec fallback)
DB_HOST = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB", "neoshield_fraud")
DB_USER = os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "analyst_user")
DB_PASS = os.getenv("DB_PASS") or os.getenv("POSTGRES_PASSWORD", "FintechSecurePassword2026")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

class TransactionPayload(BaseModel):
    user_id: int
    card_id: int
    amount: float
    currency: str = "EUR"
    merchant_category: str
    merchant_country: str
    kyc_status: str
    lat: float
    lon: float

@app.get("/")
def health_check():
    return {"status": "ok", "service": "NeoShield Engine", "model_loaded": model is not None}

@app.post("/api/v1/transactions/evaluate")
def evaluate_transaction(payload: TransactionPayload):
    if model is None:
        raise HTTPException(status_code=500, detail="Modèle ML non chargé.")

    # 1. Feature Engineering (aligné sur l'entraînement)
    high_risk_countries = ['KY', 'PA', 'PR', 'RU', 'NG']
    high_risk_categories = ['crypto', 'casino', 'gambling']

    is_high_risk_country = 1 if payload.merchant_country in high_risk_countries else 0
    is_crypto_or_casino = 1 if payload.merchant_category in high_risk_categories else 0

    time_diff = 999999.0
    distance_km = 0.0
    speed_kmh = 0.0

    # 2. Prédiction XGBoost
    df_features = pd.DataFrame({
        'amount': [payload.amount],
        'time_diff': [time_diff],
        'distance_km': [distance_km],
        'speed_kmh': [speed_kmh],
        'is_high_risk_country': [is_high_risk_country],
        'is_crypto_or_casino': [is_crypto_or_casino]
    })

    ai_risk_score = float(model.predict_proba(df_features)[0][1])

    # 3. Règles métier hybrides
    triggered_rules = []
    if is_high_risk_country:
        triggered_rules.append("HIGH_RISK_COUNTRY")
    if is_crypto_or_casino:
        triggered_rules.append("SUSPICIOUS_MERCHANT_CATEGORY")
    if payload.amount > 5000:
        triggered_rules.append("HIGH_AMOUNT_TRANSACTION")

    # Décision & flag is_fraud (1 pour BLOCK, 0 pour ALLOW/FLAG)
    if ai_risk_score > 0.7 or "HIGH_RISK_COUNTRY" in triggered_rules:
        action = "BLOCK"
        is_fraud_val = 1
    elif ai_risk_score > 0.3 or len(triggered_rules) > 0:
        action = "FLAG"
        is_fraud_val = 0
    else:
        action = "ALLOW"
        is_fraud_val = 0

    # Generer un ID de transaction unique et capturer l'heure exacte
    tx_id = f"TX_API_{uuid.uuid4().hex[:8]}"
    current_time = datetime.utcnow()

    # 4. Insertion PostgreSQL dans la table 'transactions'
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        insert_query = """
            INSERT INTO transactions (
                transaction_id, card_id, timestamp, amount, 
                latitude, longitude, merchant_country, merchant_category, is_fraud
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        
        cur.execute(insert_query, (
            tx_id,
            str(payload.card_id),
            current_time,
            payload.amount,
            payload.lat,
            payload.lon,
            payload.merchant_country,
            payload.merchant_category,
            is_fraud_val
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"--> [DB SUCCESS] Transaction {tx_id} insérée dans PostgreSQL !")
    except Exception as e:
        print(f"--> [DB ERROR] Échec de l'insertion SQL: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur d'insertion DB: {str(e)}")

    return {
        "status": "success",
        "transaction_id": tx_id,
        "action": action,
        "risk_score": round(ai_risk_score, 4),
        "triggered_rules": triggered_rules,
        "evaluated_at": current_time.isoformat()
    }