import os
import psycopg

if __name__ == "__main__":
    url: str = os.environ.get("DB_URL")
    
    if not url:
        raise ValueError("DB_URL is not set")
    
    # Connect to an existing database
    with psycopg.connect(url) as conn:
        # Open a cursor to perform database operations
        with conn.cursor() as cur:

            # Execute a command: this creates a new table
            cursor_result = cur.execute("""
                SELECT * FROM test.chat_memory;
                """)
            record = cursor_result.fetchone()
            print(record)
            print(record[2], type(record[2]))
            