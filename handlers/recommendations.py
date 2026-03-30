from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from services.movie_service import MovieService
from services.user_service import UserService
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.message(F.text == "💡 Tavsiyalar")
async def recommendations_handler(message: types.Message, session: AsyncSession):
    user_service = UserService(session)
    movie_service = MovieService(session)
    
    user = await user_service.get_or_create_user(message.from_user.id, "", "")
    recs = await movie_service.get_recommendations(user.id, limit=5)
    
    if not recs:
        await message.answer("💡 Hozircha tavsiyalar yo'q. Ko'proq kino ko'ring!")
        return
        
    text = "💡 <b>Sizga yoqishi mumkin bo'lgan kinolar:</b>\n\n"
    builder = InlineKeyboardBuilder()
    for i, m in enumerate(recs, 1):
        text += f"{i}. {m.title} (<code>{m.code}</code>)\n"
        builder.button(text=f"{i}", callback_data=f"view_movie:{m.code}")
        
    builder.adjust(5)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
