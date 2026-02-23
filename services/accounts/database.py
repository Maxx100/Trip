import os
import psycopg2
from psycopg2.extras import RealDictCursor
import time

def get_db_connection():
    # Retry logic for waiting for DB to be ready
    while True:
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'accounts_db'),
                database=os.getenv('DB_NAME', 'accounts_db'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASS', 'postgres')
            )
            return conn
        except psycopg2.OperationalError:
            print("Database not ready yet, retrying in 1 second...")
            time.sleep(1)

def create_user(email, password_hash):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO accounts (email, password_hash) VALUES (%s, %s) RETURNING id;",
            (email, password_hash)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        print(f"User created with ID: {user_id}")
        return user_id
    except Exception as e:
        conn.rollback()
        print(f"Error creating user: {e}")
        return None
    finally:
        cur.close()
        conn.close()
