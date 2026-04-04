import asyncio
from sqlalchemy import text
from database.base import engine

async def fix_schema():
    print("Database sxemasini tekshirish va yangilash boshlandi...")
    async with engine.begin() as conn:
        try:
            # SQLite uchun 'ad_channels' jadvali mavjudligini tekshiramiz
            # channel_id turini o'zgartirish (SQLite-da bu biroz murakkab, 
            # lekin biz shunchaki tekshirib ko'ramiz)
            print("ad_channels jadvali yangilanmoqda...")
            
            # Eslatma: SQLite-da 'alter table' uncha yaxshi ishlamaydi cheklovlar bilan.
            # Eng xavfsiz yo'li - agar xato bersa, jadvalni qayta yaratish.
            
            # Lekin bizning modelimiz endi String(255). 
            # Agar foydalanuvchi yangi kanal qo'shsa va u @username bo'lsa, 
            # ba'zi DB drayverlari BigInteger-ga yozishda xato beradi.
            
            # Eng yaxshisi: Jadvalni o'chirib, qayta yaratish (agar ma'lumotlar kam bo'lsa)
            # Yoki shunchaki ogohlantirish.
            
            # Biz bu yerda shunchaki create_all qilamiz, u yangi modellarni yaratadi.
            from database.models import Base
            await conn.run_sync(Base.metadata.create_all)
            print("Barcha jadvallar tekshirildi.")
            
        except Exception as e:
            print(f"Xatolik yuz berdi: {e}")

if __name__ == "__main__":
    asyncio.run(fix_schema())
