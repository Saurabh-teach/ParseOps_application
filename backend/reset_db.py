import psycopg2
from psycopg2 import OperationalError

def reset_db():
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user='postgres',
            password='postgres',
            host='127.0.0.1',
            port='5432'
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Kill other connections to the DB
        cur.execute("""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = 'parseops'
              AND pid <> pg_backend_pid();
        """)
        
        cur.execute("DROP DATABASE IF EXISTS parseops")
        cur.execute("CREATE DATABASE parseops")
        print("Database 'parseops' has been reset successfully.")
        
        cur.close()
        conn.close()
    except OperationalError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    reset_db()
