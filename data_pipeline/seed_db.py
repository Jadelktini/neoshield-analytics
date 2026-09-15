import os
import sys
from pathlib import Path
import pandas as pd
import psycopg2
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()

sys.path.append(str(Path(__file__).resolve().parent.parent))

from data_pipeline.generate_synthetic_data import generate_fraud_dataset

def seed_database():
    csv_path = Path("data_pipeline/synthetic_transactions.csv")
    
    if not csv_path.exists():
        print("⚠️ Fichier CSV introuvable, génération en cours...")
        df = generate_fraud_dataset()
    else:
        df = pd.read_csv(csv_path)

    lat_col = 'latitude' if 'latitude' in df.columns else 'lat'
    lon_col = 'longitude' if 'longitude' in df.columns else 'lon'

    # Mapping sécurisé sans mot de passe en clair dans le code
    host = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB", "neoshield_fraud")
    user = os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "analyst_user")
    password = os.getenv("DB_PASS") or os.getenv("POSTGRES_PASSWORD")

    # Vérification explicite du mot de passe
    if not password:
        raise ValueError(
            "❌ Erreur de sécurité : Aucun mot de passe trouvé. "
            "Veuillez définir DB_PASS ou POSTGRES_PASSWORD dans votre fichier .env."
        )

    print(f"🔌 Connexion à PostgreSQL ({host}:{port}) pour la base '{db}' avec l'utilisateur '{user}'...")
    
    try:
        conn = psycopg2.connect(
            host=host, port=port, dbname=db, user=user, password=password
        )
    except psycopg2.OperationalError as e:
        print("\n❌ Échec de connexion à PostgreSQL.")
        print("👉 Vérifiez que le conteneur Docker PostgreSQL est bien démarré et que les identifiants correspondent.")
        raise e

    cursor = conn.cursor()

    # Recréation propre de la table transactions
    print("🧹 Préparation de la table 'transactions'...")
    cursor.execute("DROP TABLE IF EXISTS transactions;")
    cursor.execute("""
        CREATE TABLE transactions (
            transaction_id VARCHAR(50) PRIMARY KEY,
            card_id VARCHAR(50),
            timestamp TIMESTAMP,
            amount NUMERIC(10, 2),
            latitude FLOAT,
            longitude FLOAT,
            merchant_country VARCHAR(10),
            merchant_category VARCHAR(50),
            is_fraud INT
        );
    """)

    print("🌱 Insertion des transactions en base de données...")
    insert_query = """
    INSERT INTO transactions (
        transaction_id, card_id, timestamp, amount, latitude, longitude, 
        merchant_country, merchant_category, is_fraud
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    records = []
    for _, row in df.iterrows():
        records.append((
            str(row['transaction_id']),
            str(row['card_id']),
            str(row['timestamp']),
            float(row['amount']),
            float(row[lat_col]),
            float(row[lon_col]),
            str(row['merchant_country']),
            str(row['merchant_category']),
            int(row['is_fraud'])
        ))

    cursor.executemany(insert_query, records)
    conn.commit()
    cursor.close()
    conn.close()

    print(f"✅ {len(records)} transactions insérées avec succès dans PostgreSQL !")

if __name__ == "__main__":
    seed_database()