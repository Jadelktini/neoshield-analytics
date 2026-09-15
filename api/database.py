import psycopg2
from psycopg2.extras import RealDictCursor
from api.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

def get_db_connection():
    """Crée et retourne une connexion à la base de données PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            connect_timeout=3
        )
        return conn
    except Exception as e:
        print(f"⚠️ Erreur de connexion PostgreSQL : {e}")
        return None