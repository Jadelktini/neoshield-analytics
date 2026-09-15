import os
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "neoshield_fraud")
DB_USER = os.getenv("DB_USER", "analyst_user")
DB_PASS = os.getenv("DB_PASS", "FintechSecurePassword2026")

API_ENV = os.getenv("API_ENV", "development")