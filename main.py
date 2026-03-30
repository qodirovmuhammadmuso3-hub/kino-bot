import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Routerlar
from handlers import meta, movies, watchlist, ratings, history, filters, notifications, inline, admin, recommendations, sync
# Middlewarelar
from middlewares.db_session import DbSessionMiddleware
from middlewares.throttling import ThrottlingMiddleware
from aiohttp import web
import asyncio
# DB
from database.base import engine, Base

load_dotenv()

async def on_startup():
    # DB jadvallarini yaratish (PostgreSQL/SQLite)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("Database tables created.")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("BOT_TOKEN topilmadi!")

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Middlewarelarni ro'yxatdan o'tkazish
    from middlewares.subscription import SubscriptionMiddleware
    dp.message.middleware(ThrottlingMiddleware())
    dp.message.middleware(DbSessionMiddleware())
    dp.message.middleware(SubscriptionMiddleware())
    
    dp.callback_query.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())
    
    dp.inline_query.middleware(DbSessionMiddleware())
    dp.channel_post.middleware(DbSessionMiddleware())

    # Routerlarni ulash
    dp.include_routers(
        meta.router,
        movies.router,
        watchlist.router,
        ratings.router,
        history.router,
        filters.router,
        notifications.router,
        inline.router,
        admin.router,
        recommendations.router,
        sync.router
    )

    await on_startup()
    logging.info("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
