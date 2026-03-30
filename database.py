import aiosqlite
import datetime
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_PATH = "database.sqlite"
ADMIN_ID = os.getenv("ADMIN_ID")

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                movie_code TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                release_year TEXT,
                genre TEXT,
                duration TEXT,
                file_id TEXT NOT NULL,
                post_link TEXT,
                source_channel TEXT,
                is_series BOOLEAN DEFAULT FALSE,
                episode_number INTEGER,
                content_type TEXT DEFAULT 'movie',
                media_type TEXT DEFAULT 'video',
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                request_count INTEGER DEFAULT 0
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ad_channels (
                channel_id TEXT PRIMARY KEY,
                channel_link TEXT NOT NULL,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def get_ad_channels():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT channel_id, channel_link FROM ad_channels') as cursor:
            rows = await cursor.fetchall()
            return [{"id": row["channel_id"], "link": row["channel_link"]} for row in rows]

async def add_ad_channel(channel_id, channel_link):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT OR REPLACE INTO ad_channels (channel_id, channel_link, date_added)
            VALUES (?, ?, ?)
        ''', (channel_id, channel_link, datetime.datetime.now()))
        await db.commit()

async def remove_ad_channel(channel_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('DELETE FROM ad_channels WHERE channel_id = ?', (channel_id,))
        await db.commit()

async def get_next_movie_code(content_type="movie"):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT movie_code FROM movies 
            WHERE content_type = ? AND movie_code GLOB '[0-9]*'
            ORDER BY CAST(movie_code AS INTEGER) DESC LIMIT 1
        ''', (content_type,))
        row = await cursor.fetchone()
        
        if not row:
            return "001" if content_type == "movie" else "1"
        
        last_code = int(row['movie_code'])
        next_val = last_code + 1
        if content_type == "movie":
            return str(next_val).zfill(3)
        return str(next_val)

async def add_user(user_id, full_name, username):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO users (user_id, full_name, username, last_active)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (user_id) DO UPDATE SET
                full_name = EXCLUDED.full_name,
                username = EXCLUDED.username,
                last_active = EXCLUDED.last_active
        ''', (user_id, full_name, username, datetime.datetime.now()))
        await db.commit()

async def get_stats():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('SELECT COUNT(*) FROM users') as cursor:
            total_users = await cursor.fetchone()
        async with db.execute('SELECT COUNT(*) FROM movies') as cursor:
            total_movies = await cursor.fetchone()
        return total_users[0], total_movies[0]

async def get_all_users():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT user_id FROM users') as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def add_movie(movie_code, title, year, genre, duration, file_id, post_link, source_channel, is_series=False, episode_number=None, content_type="movie", media_type="video"):
    search_code = str(movie_code).strip()
    if content_type == "movie" and search_code.isdigit() and len(search_code) < 3:
        search_code = search_code.zfill(3)
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT OR IGNORE INTO movies (
                movie_code, title, release_year, genre, duration, file_id, post_link, source_channel, 
                is_series, episode_number, content_type, media_type, date_added, request_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (search_code, title.strip(), year, genre, duration, file_id, post_link, source_channel,
              is_series, episode_number, content_type, media_type, datetime.datetime.now(), 0))
        await db.commit()

async def get_episodes(title):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''
            SELECT * FROM movies WHERE title = ? AND is_series = 1 ORDER BY episode_number ASC
        ''', (title.strip(),)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_movie_by_code(code: str, content_type: str | None = None):
    search_code = str(code).strip()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        if content_type:
            async with db.execute('SELECT * FROM movies WHERE movie_code = ? AND content_type = ?', (search_code, content_type)) as cursor:
                row = await cursor.fetchone()
        else:
            async with db.execute('SELECT * FROM movies WHERE movie_code = ?', (search_code,)) as cursor:
                row = await cursor.fetchone()
        
        if row:
            return dict(row)
        
        # Padding search
        if (not content_type or content_type == "movie") and search_code.isdigit() and len(search_code) < 3:
            padded_code = search_code.zfill(3)
            async with db.execute('SELECT * FROM movies WHERE movie_code = ? AND content_type = "movie"', (padded_code,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                
    return None

async def search_movies(query, content_type=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        sql = 'SELECT * FROM movies WHERE title LIKE ?'
        params = [f'%{query}%']
        if content_type:
            sql += ' AND content_type = ?'
            params.append(content_type)
        sql += ' LIMIT 10'
        
        async with db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def increment_request_count(movie_code):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('UPDATE movies SET request_count = request_count + 1 WHERE movie_code = ?', (str(movie_code),))
        await db.commit()

async def get_latest_movies(limit=10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT title, movie_code FROM movies ORDER BY date_added DESC LIMIT ?', (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [(row['title'], row['movie_code']) for row in rows]

async def get_top_movies(limit=10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT title, movie_code FROM movies ORDER BY request_count DESC LIMIT ?', (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [(row['title'], row['movie_code']) for row in rows]

async def update_movie_field(movie_code, update_data):
    if not update_data:
        return
    async with aiosqlite.connect(DATABASE_PATH) as db:
        set_clauses = [f"{k} = ?" for k in update_data.keys()]
        sql = f"UPDATE movies SET {', '.join(set_clauses)} WHERE movie_code = ?"
        params = list(update_data.values()) + [str(movie_code)]
        await db.execute(sql, params)
        await db.commit()
async def get_genres(content_type=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        sql = 'SELECT DISTINCT genre FROM movies WHERE genre != "Noma\'lum"'
        params = []
        if content_type:
            sql += ' AND content_type = ?'
            params.append(content_type)
        async with db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows if row[0]]

async def get_years(content_type=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        sql = 'SELECT DISTINCT release_year FROM movies WHERE release_year != "0" AND release_year != "Noma\'lum"'
        params = []
        if content_type:
            sql += ' AND content_type = ?'
            params.append(content_type)
        sql += ' ORDER BY release_year DESC'
        async with db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows if row[0]]

async def get_movies_by_genre(genre, content_type=None, limit=20):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        sql = 'SELECT * FROM movies WHERE genre = ?'
        params = [genre]
        if content_type:
            sql += ' AND content_type = ?'
            params.append(content_type)
        sql += ' LIMIT ?'
        params.append(limit)
        async with db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_movies_by_year(year, content_type=None, limit=20):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        sql = 'SELECT * FROM movies WHERE release_year = ?'
        params = [year]
        if content_type:
            sql += ' AND content_type = ?'
            params.append(content_type)
        sql += ' LIMIT ?'
        params.append(limit)
        async with db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
