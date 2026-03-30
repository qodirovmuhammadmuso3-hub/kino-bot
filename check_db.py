import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from database.models import BotSetting

async def check_settings():
    engine = create_async_engine("sqlite+aiosqlite:///bot_database.db")
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        result = await session.execute(select(BotSetting))
        settings = result.scalars().all()
        for s in settings:
            print(f"{s.name}: {s.value}")

if __name__ == "__main__":
    asyncio.run(check_settings())
