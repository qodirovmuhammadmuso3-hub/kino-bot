import asyncio
import os
from aiogram import Bot
from dotenv import load_dotenv

async def clear_webhook():
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("BOT_TOKEN topilmadi!")
        return
        
    bot = Bot(token=token)
    try:
        info = await bot.get_webhook_info()
        print(f"Hozirgi Webhook holati: {info}")
        
        if info.url:
            print("Webhook'ni o'chirmoqdaman...")
            await bot.delete_webhook(drop_pending_updates=True)
            print("Webhook muvaffaqiyatli o'chirildi!")
        else:
            print("Webhook allaqachon o'chirilgan.")
            
        me = await bot.get_me()
        print(f"Bot ma'lumotlari: @{me.username} (ID: {me.id})")
        
    except Exception as e:
        print(f"Xatolik: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(clear_webhook())
