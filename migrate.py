import asyncio
import aiosqlite
import logging
from database.base import AsyncSessionLocal, engine, Base
from database.models import User, Movie
from sqlalchemy import select

async def migrate():
    logging.basicConfig(level=logging.INFO)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    OLD_DB_PATH = "database.sqlite"
    async with aiosqlite.connect(OLD_DB_PATH) as db:
        async with AsyncSessionLocal() as session:
            # Kinolarni o'chirish
            cursor = await db.execute("SELECT * FROM movies")
            old_movies = await cursor.fetchall()
            movie_count = 0
            for m in old_movies:
                # movies: id(0), title(1), file_id(2), code(3), description(4)
                code_val = str(m[3])
                title_val = str(m[1])
                desc_val = str(m[4]) if m[4] else ""
                file_id_val = str(m[2])

                stmt = select(Movie).where(Movie.code == code_val)
                res = await session.execute(stmt)
                if res.scalar_one_or_none(): continue
                    
                new_movie = Movie(
                    code=code_val,
                    title=title_val,
                    description=desc_val,
                    file_id=file_id_val,
                    media_type='video',
                    is_series=False
                )
                session.add(new_movie)
                movie_count += 1
            
            # Foydalanuvchilar (ixtiyoriy)
            try:
                cursor = await db.execute("SELECT * FROM users")
                old_users = await cursor.fetchall()
                for u in old_users:
                    # users: user_id(0), username(1), full_name(2)
                    stmt = select(User).where(User.user_id == u[0])
                    res = await session.execute(stmt)
                    if res.scalar_one_or_none(): continue
                    session.add(User(user_id=u[0], username=u[1] or "", full_name=u[2] or f"User {u[0]}"))
            except: pass
                
            await session.commit()
            logging.info(f"Migration successful! {movie_count} movies moved.")

if __name__ == "__main__":
    asyncio.run(migrate())
