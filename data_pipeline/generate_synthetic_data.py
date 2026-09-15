import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

def generate_fraud_dataset(n_samples=10000):
    np.random.seed(42)
    start_date = datetime(2026, 8, 1)
    
    card_ids = np.random.randint(1000, 1500, size=n_samples)
    timestamps = [start_date + timedelta(seconds=int(x)) for x in np.random.randint(0, 30*24*3600, size=n_samples)]
    amounts = np.round(np.random.exponential(scale=50, size=n_samples) + 2.0, 2)
    latitudes = np.random.normal(loc=45.5017, scale=0.5, size=n_samples)
    longitudes = np.random.normal(loc=-73.5673, scale=0.5, size=n_samples)
    countries = np.random.choice(['CA', 'US', 'FR', 'KY', 'PA', 'RU'], size=n_samples, p=[0.7, 0.15, 0.08, 0.03, 0.02, 0.02])
    categories = np.random.choice(['retail', 'grocery', 'travel', 'crypto', 'casino'], size=n_samples, p=[0.5, 0.3, 0.1, 0.05, 0.05])
    
    df = pd.DataFrame({
        'transaction_id': [f"TX_{i:06d}" for i in range(n_samples)],
        'card_id': card_ids,
        'timestamp': timestamps,
        'amount': amounts,
        'latitude': latitudes,
        'longitude': longitudes,
        'merchant_country': countries,
        'merchant_category': categories
    }).sort_values(by=['card_id', 'timestamp']).reset_index(drop=True)
    
    # --- Ajout direct des colonnes dérivées ---
    df['time_diff'] = df.groupby('card_id')['timestamp'].diff().dt.total_seconds().fillna(999999)
    prev_lat = df.groupby('card_id')['latitude'].shift(1).fillna(df['latitude'])
    prev_lon = df.groupby('card_id')['longitude'].shift(1).fillna(df['longitude'])
    
    df['distance_km'] = haversine(df['latitude'], df['longitude'], prev_lat, prev_lon)
    df['speed_kmh'] = (df['distance_km'] / (df['time_diff'] / 3600)).fillna(0).replace([np.inf, -np.inf], 0)
    
    df['is_high_risk_country'] = df['merchant_country'].isin(['KY', 'PA', 'RU', 'NG']).astype(int)
    df['is_crypto_or_casino'] = df['merchant_category'].isin(['crypto', 'casino']).astype(int)
    
    # Label de fraude (règle synthétique)
    df['is_fraud'] = ((df['speed_kmh'] > 800) | (df['is_high_risk_country'] == 1) & (df['amount'] > 500)).astype(int)
    
    # Export CSV
    output_path = Path("data_pipeline/synthetic_transactions.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✅ Dataset généré avec succès dans '{output_path}' ({len(df)} lignes).")
    
    return df