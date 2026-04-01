from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Database URL va sozlamalar
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot_database.db")

# MySQL uchun SSL va ulanish parametrlarini sozlash
connect_args = {}
if "mysql" in DATABASE_URL:
    # URL'dan ssl parametrini olib tashlab, connect_args orqali yuborish (aiomysql uchun)
    if "ssl=true" in DATABASE_URL.lower():
        DATABASE_URL = DATABASE_URL.replace("ssl=true", "").replace("SSL=true", "").rstrip("?&")
        connect_args["ssl"] = True

engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    pool_pre_ping=True, 
    pool_recycle=3600,
    connect_args=connect_args
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
