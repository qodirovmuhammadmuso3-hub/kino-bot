import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database.models import BotSetting, AdChannel
from sqlalchemy import select
import os
from dotenv import load_dotenv

load_dotenv()

async def check():
    engine = create_async_engine(os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot_database.db"))
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Settings
        res = await session.execute(select(BotSetting))
        settings = res.scalars().all()
        print("--- Bot Settings ---")
        for s in settings:
            print(f"{s.key}: {s.value}")
            
        # Ad Channels
        res = await session.execute(select(AdChannel))
        channels = res.scalars().all()
        print("\n--- Ad Channels ---")
        for c in channels:
            print(f"ID: {c.channel_id} | Link: {c.link}")

if __name__ == "__main__":
    asyncio.run(check())
