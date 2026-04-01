import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from aiohttp import web

# Handlers
from handlers import meta, movies, watchlist, ratings, history, filters, notifications, inline, admin, recommendations, sync
# Middlewarelar
from middlewares.db_session import DbSessionMiddleware
from middlewares.throttling import ThrottlingMiddleware
# DB
from database.base import engine, Base

load_dotenv()

async def main():
    # Logging sozlamalari
    logging.basicConfig(level=logging.INFO)

    # MB jadvallarini yaratish
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("Database tables created.")

    bot = Bot(
        token=os.getenv("BOT_TOKEN"),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
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

    # Routerni ulash
    dp.include_routers(
        admin.router,
        sync.router,
        meta.router,
        filters.router,
        watchlist.router,
        ratings.router,
        history.router,
        notifications.router,
        recommendations.router,
        movies.router,
        inline.router
    )

    logging.info("Bot is starting...")
    
    # Render uchun dummy web server (Free tier uchun port kerak)
    async def handle(request):
        return web.Response(text="Bot is running!")

    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    logging.info(f"Starting web server on port {port}")
    
    # Self-ping funksiyasi (Render uxlab qolmasligi uchun)
    async def keep_alive():
        url = os.getenv("RENDER_EXTERNAL_URL")
        if not url:
            logging.info("Self-ping: RENDER_EXTERNAL_URL topilmadi, o'tkazib yuborildi.")
            return
            
        import aiohttp
        logging.info(f"Self-ping task started for: {url}")
        while True:
            await asyncio.sleep(600) # Har 10 daqiqada
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            logging.info("Self-ping: Muvaffaqiyatli (200 OK)")
            except Exception as e:
                logging.error(f"Self-ping xatolik: {e}")

    await asyncio.gather(
        site.start(),
        dp.start_polling(bot),
        keep_alive()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
