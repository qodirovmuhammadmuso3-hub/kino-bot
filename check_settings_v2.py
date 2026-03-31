import sqlite3

def check_settings():
    try:
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.fetchall()
        print(f"Total settings found: {len(rows)}")
        for row in rows:
            print(f"Key: [{row[0]}] Value: [{row[1]}]")
        conn.close()
    except Exception as e:
        print(f"Error checking settings: {e}")

if __name__ == "__main__":
    check_settings()
