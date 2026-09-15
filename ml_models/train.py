import os
import sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from xgboost import XGBClassifier

# Ajout de la racine du projet au path Python pour garantir les imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from data_pipeline.generate_synthetic_data import generate_fraud_dataset

def train_and_save_model():
    print("🔄 Génération du dataset de travail...")
    df = generate_fraud_dataset(n_samples=10000)
    
    # Définition des features (X) et de la cible (y)
    features = [
        'amount', 
        'time_diff', 
        'distance_km', 
        'speed_kmh', 
        'is_high_risk_country', 
        'is_crypto_or_casino'
    ]
    
    X = df[features]
    y = df['is_fraud']
    
    # Séparation train/test (correction du paramètre test_size)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Gestion du déséquilibre de classes pour XGBoost
    scale_pos_weight = (len(y_train) - sum(y_train)) / sum(y_train)
    
    print("🤖 Entraînement du modèle XGBoost...")
    model = XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.05,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)
    
    # Évaluation
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    auc_score = roc_auc_score(y_test, y_proba)
    print(f"\n📊 ROC-AUC Score: {auc_score:.4f}")
    print("\nRapport de classification :")
    print(classification_report(y_test, y_pred))
    
    # Sauvegarde de l'artefact
    output_dir = Path("ml_models")
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "fraud_detector_model.pkl"
    
    joblib.dump(model, model_path)
    print(f"✅ Modèle sauvegardé avec succès dans : {model_path}\n")

if __name__ == "__main__":
    train_and_save_model()