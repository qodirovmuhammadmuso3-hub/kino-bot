import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from services.movie_service import MovieService
from database.models import Movie
from sqlalchemy import select
import os
from dotenv import load_dotenv

load_dotenv()

# UTF-8 for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def debug():
    engine = create_async_engine(os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot.db"))
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        movie_service = MovieService(session)
        
        # 1. DB dagi hamma kinolarni ko'rish
        res = await session.execute(select(Movie))
        movies = res.scalars().all()
        print(f"Bazada jami {len(movies)} ta kino bor.\n")
        
        for m in movies:
            print(f"ID: {m.id} | Code: [{m.code}] | Title: {m.title} | Type: {m.content_type}")
            
        print("\n--- QIDIRUV TESTI ---")
        test_codes = ["1", "001", " 1 ", "123", "T101"]
        for tc in test_codes:
            result = await movie_service.get_movie_by_code(tc)
            if result:
                print(f"✅ Qidiruv '{tc}' -> Topildi: {result.title} ({result.content_type} / Code: {result.code})")
            else:
                print(f"❌ Qidiruv '{tc}' -> Topilmadi.")

if __name__ == "__main__":
    asyncio.run(debug())
