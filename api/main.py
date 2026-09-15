from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import joblib
import pandas as pd
from datetime import datetime
import os

# Import des configurations sécurisées
from api.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

app = FastAPI(
    title="NeoShield Analytics API",
    description="API temps réel de détection de fraude et scoring de risque par carte bancaire",
    version="1.0.0"
)

# Chargement du modèle XGBoost
MODEL_PATH = "ml_models/fraud_detector_model.pkl"
try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    model = None
    print(f"⚠️ Avertissement : Impossible de charger le modèle ML depuis {MODEL_PATH} ({e})")

# Schemas Pydantic
class TransactionPayload(BaseModel):
    user_id: int
    card_id: int
    amount: float = Field(..., gt=0, description="Montant de la transaction")
    currency: str = "EUR"
    merchant_category: str
    merchant_country: str
    kyc_status: Optional[str] = "verified"
    lat: float
    lon: float

class EvaluationResponse(BaseModel):
    status: str
    transaction_id: str
    action: str
    risk_score: float
    triggered_rules: List[str]
    evaluated_at: str

def get_db_connection():
    try:
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur de connexion à la base de données: {str(e)}"
        )

@app.get("/")
def health_check():
    return {"status": "online", "service": "NeoShield Analytics Engine"}

@app.post("/api/v1/transactions/evaluate", response_model=EvaluationResponse)
def evaluate_transaction(payload: TransactionPayload):
    triggered_rules = []
    
    # 1. Moteur de règles métier
    high_risk_countries = ["KY", "PR", "VG", "IR", "KP"]
    suspicious_categories = ["crypto", "casino", "wire_transfer"]
    
    if payload.merchant_country.upper() in high_risk_countries:
        triggered_rules.append("HIGH_RISK_COUNTRY")
        
    if payload.merchant_category.lower() in suspicious_categories:
        triggered_rules.append("SUSPICIOUS_MERCHANT_CATEGORY")
        
    if payload.amount > 5000.00:
        triggered_rules.append("HIGH_AMOUNT_TRANSACTION")

    # 2. Inférence du modèle Machine Learning (XGBoost)
    risk_score = 0.05
    if model is not None:
        try:
            # Structuration des features pour le modèle
            features_df = pd.DataFrame([{
                'amount': payload.amount,
                'lat': payload.lat,
                'lon': payload.lon,
                'is_high_risk_country': 1 if payload.merchant_country.upper() in high_risk_countries else 0,
                'is_suspicious_category': 1 if payload.merchant_category.lower() in suspicious_categories else 0
            }])
            probabilities = model.predict_proba(features_df)
            risk_score = float(probabilities[0][1])
        except Exception as e:
            risk_score = 0.50
            triggered_rules.append("MODEL_INFERENCE_FALLBACK")

    # 3. Moteur de Décision Hybride
    if risk_score >= 0.80 or "HIGH_RISK_COUNTRY" in triggered_rules:
        action = "BLOCK"
    elif risk_score >= 0.40 or len(triggered_rules) > 0:
        action = "FLAG"
    else:
        action = "ALLOW"

    tx_id = f"TX_API_{os.urandom(4).hex()}"
    evaluated_at = datetime.utcnow().isoformat()

    # 4. Persistance PostgreSQL
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        is_fraud_val = 1 if action == "BLOCK" else 0
        cursor.execute("""
            INSERT INTO transactions (
                transaction_id, card_id, timestamp, amount, latitude, longitude,
                merchant_country, merchant_category, is_fraud
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            tx_id, str(payload.card_id), evaluated_at, payload.amount,
            payload.lat, payload.lon, payload.merchant_country,
            payload.merchant_category, is_fraud_val
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur d'enregistrement PostgreSQL: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()

    return EvaluationResponse(
        status="success",
        transaction_id=tx_id,
        action=action,
        risk_score=round(risk_score, 4),
        triggered_rules=triggered_rules,
        evaluated_at=evaluated_at
    )