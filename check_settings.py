import sqlite3

def check_settings():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT key, value FROM bot_settings")
        rows = cursor.fetchall()
        print("Settings in DB:")
        for row in rows:
            print(f"Key: {row[0]}, Value: {row[1]}")
            
        cursor.execute("SELECT * FROM ad_channels")
        chans = cursor.fetchall()
        print("\nAd Channels in DB:")
        for ch in chans:
            print(ch)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_settings()
