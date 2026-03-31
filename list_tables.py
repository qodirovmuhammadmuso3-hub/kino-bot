import sqlite3

def list_tables():
    try:
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables in database: {[t[0] for t in tables]}")
        for table in tables:
            table_name = table[0]
            print(f"\nSchema for {table_name}:")
            cursor.execute(f"PRAGMA table_info({table_name})")
            info = cursor.fetchall()
            for col in info:
                print(col)
        conn.close()
    except Exception as e:
        print(f"Error listing tables: {e}")

if __name__ == "__main__":
    list_tables()
