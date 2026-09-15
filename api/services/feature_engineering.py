import numpy as np
import pandas as pd
from typing import Dict, Any

def extract_transaction_features(payload: Dict[str, Any], historical_stats: Dict[str, Any]) -> pd.DataFrame:
    """
    Transforme le payload reçu et l'historique de la DB en un DataFrame 
    prêt à être consommé par le modèle XGBoost.
    """
    velocity_kmh = historical_stats.get("velocity_kmh", 0.0)
    tx_count_10m = historical_stats.get("tx_count_10m", 0)
    avg_amount_30d = historical_stats.get("avg_amount_30d", payload["amount"])
    std_amount_30d = historical_stats.get("std_amount_30d", 1.0)
    
    # Calcul du Z-Score du montant
    amount_zscore = (payload["amount"] - avg_amount_30d) / (std_amount_30d if std_amount_30d > 0 else 1.0)
    
    features = {
        "amount": [payload["amount"]],
        "amount_zscore": [amount_zscore],
        "velocity_kmh": [velocity_kmh],
        "tx_count_10m": [tx_count_10m],
        "is_foreign_country": [1 if payload["merchant_country"] != "FR" else 0],
        "is_high_risk_category": [1 if payload["merchant_category"] in ["gambling", "crypto", "electronics"] else 0]
    }
    
    return pd.DataFrame(features)