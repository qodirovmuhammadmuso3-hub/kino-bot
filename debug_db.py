import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from database.models import User, Movie, Watchlist, History

async def check_db():
    engine = create_async_engine("sqlite+aiosqlite:///bot.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check users
        res = await session.execute(select(User))
        users = res.scalars().all()
        print(f"Total Users: {len(users)}")
        for u in users:
            print(f"User: {u.user_id} (DB ID: {u.id}), Admin: {u.is_admin}")
            
        # Check watchlist
        res = await session.execute(select(Watchlist))
        items = res.scalars().all()
        print(f"Total Watchlist Items: {len(items)}")
        for i in items:
            print(f"Watchlist: User DB ID {i.user_id}, Movie ID {i.movie_id}")
            
        # Check movies
        res = await session.execute(select(Movie))
        movies = res.scalars().all()
        print(f"Total Movies: {len(movies)}")
        for m in movies:
            print(f"Movie: {m.title} (ID: {m.id}, Code: {m.code})")

if __name__ == "__main__":
    asyncio.run(check_db())
