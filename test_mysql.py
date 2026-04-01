import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

async def test_mysql():
    url = os.getenv("DATABASE_URL")
    print(f"Testing connection to: {url.split('@')[1] if '@' in url else url}")
    
    # SSL yechimi
    connect_args = {}
    if "ssl=true" in url.lower():
        url = url.replace("ssl=true", "").replace("SSL=true", "").rstrip("?&")
        connect_args["ssl"] = True
    
    try:
        engine = create_async_engine(
            url, 
            echo=True,
            connect_args=connect_args
        )
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            result = await session.execute(text("SELECT 1"))
            print(f"Connection SUCCESS: {result.scalar()}")
            
    except Exception as e:
        print(f"Connection FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_mysql())
