import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables du fichier .env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Configuration de la base de données sans mot de passe en dur
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "neoshield_fraud")
DB_USER = os.getenv("DB_USER", "analyst_user")
DB_PASS = os.getenv("DB_PASS") or os.getenv("POSTGRES_PASSWORD")

# Vérification de sécurité au chargement de la configuration
if not DB_PASS:
    raise ValueError(
        "❌ Erreur de sécurité : Aucun mot de passe trouvé pour la base de données. "
        "Veuillez configurer la variable DB_PASS dans votre fichier .env."
    )