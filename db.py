import psycopg2
from config import DB_NAME, DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT

def get_db_connection():
    """Create a new connection to PostgreSQL."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USERNAME,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print("❌ Database Connection Error:", e)
        return None
