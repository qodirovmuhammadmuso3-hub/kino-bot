import sqlite3
import base64

def check_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT code, title, content_type FROM movies LIMIT 20")
    rows = cursor.fetchall()
    print(f"Total rows found: {len(rows)}")
    for row in rows:
        code = row[0]
        title = row[1]
        ctype = row[2]
        # Clean title to only allow ascii for printing
        ascii_title = title.encode('ascii', 'ignore').decode('ascii')
        print(f"Code: [{code}] Title: [{ascii_title}] Type: [{ctype}]")
    conn.close()

if __name__ == "__main__":
    check_db()
