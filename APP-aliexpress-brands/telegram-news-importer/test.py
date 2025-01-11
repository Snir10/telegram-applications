import sqlite3
import time

def execute_query_with_retry(query, retries=5, delay=2):
    for i in range(retries):
        try:
            conn = sqlite3.connect('your_database.db')
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            conn.close()
            return
        except sqlite3.OperationalError as e:
            if 'locked' in str(e).lower():
                print(f"Database is locked, retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                raise
