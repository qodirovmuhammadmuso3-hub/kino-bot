import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from services.movie_service import MovieService
from database.base import Base

async def test_search():
    engine = create_async_engine("sqlite+aiosqlite:///bot_database.db")
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        movie_service = MovieService(session)
        
        # Test 1: EXACT match "1"
        movie = await movie_service.get_movie_by_code("1")
        print(f"Search '1': {'FOUND' if movie else 'NOT FOUND'}")
        
        # Test 2: Padded "001"
        movie = await movie_service.get_movie_by_code("001")
        print(f"Search '001': {'FOUND' if movie else 'NOT FOUND'}")
        
        # Test 3: With prefix "kod 1"
        import re
        query = "kod 1"
        # The cleaning logic from handler:
        clean_query = re.sub(r'^(?i)(kod|id|🆔)\s*', '', query)
        movie = await movie_service.get_movie_by_code(clean_query)
        print(f"Search 'kod 1' (cleaned to '{clean_query}'): {'FOUND' if movie else 'NOT FOUND'}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_search())
