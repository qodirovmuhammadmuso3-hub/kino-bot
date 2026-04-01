from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_service import UserService
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.message(F.text == "🕒 Tarix")
async def show_history(message: types.Message, session: AsyncSession):
    user_service = UserService(session)
    user = await user_service.get_or_create_user(
        message.from_user.id, 
        message.from_user.full_name, 
        message.from_user.username or ""
    )
    
    # Oxirgi 10 tasi
    history_items = await user_service.get_user_history(user.id, limit=10)
    
    if not history_items:
        await message.answer("🕒 <b>Sizda ko'rish tarixi mavjud emas.</b>", parse_mode="HTML")
        return

    text = "🕒 <b>Oxirgi ko'rgan kinolaringiz:</b>\n\n"
    builder = InlineKeyboardBuilder()
    
    # Unikal kinolar ro'yxatini olish (bitta kinoni ko'p ko'rgan bo'lishi mumkin)
    seen_movies = []
    unique_history = []
    for item in history_items:
        if item.movie_id not in seen_movies:
            seen_movies.append(item.movie_id)
            unique_history.append(item)

    for i, item in enumerate(unique_history, 1):
        movie = item.movie
        text += f"{i}. {movie.title} (<code>{movie.code}</code>)\n"
        builder.button(text=f"{i}", callback_data=f"view_movie:{movie.code}")
    
    builder.adjust(5)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
