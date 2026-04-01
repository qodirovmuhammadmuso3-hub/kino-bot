from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from services.movie_service import MovieService
from services.user_service import UserService
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.message(F.text == "📌 Watchlist")
async def show_watchlist(message: types.Message, session: AsyncSession):
    user_service = UserService(session)
    user = await user_service.get_or_create_user(message.from_user.id, "", "")
    
    items = await user_service.get_watchlist(user.id)
    if not items:
        await message.answer("📌 <b>Sizning watchlist'ingiz bo'sh.</b>\nKino ostidagi tugmani bosib saqlab qo'yishingiz mumkin.", parse_mode="HTML")
        return

    text = "📌 <b>Siz saqlagan kinolar:</b>\n\n"
    builder = InlineKeyboardBuilder()
    for i, item in enumerate(items, 1):
        movie = item.movie
        text += f"{i}. {movie.title} (<code>{movie.code}</code>)\n"
        builder.button(text=f"{i}", callback_data=f"view_movie:{movie.code}")
    
    builder.adjust(5)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("add_watchlist:"))
async def add_watchlist_handler(callback: types.CallbackQuery, session: AsyncSession):
    movie_id = int(callback.data.split(":")[1])
    movie_service = MovieService(session)
    user_service = UserService(session)
    
    user = await user_service.get_or_create_user(callback.from_user.id, "", "")
    added = await movie_service.add_to_watchlist(user.id, movie_id)
    
    if added:
        await callback.answer("✅ Watchlist'ga qo'shildi!", show_alert=False)
    else:
        await callback.answer("⚠️ Bu allaqachon watchlist'ingizda bor.", show_alert=False)

@router.callback_query(F.data.startswith("rem_watchlist:"))
async def rem_watchlist_handler(callback: types.CallbackQuery, session: AsyncSession):
    movie_id = int(callback.data.split(":")[1])
    user_service = UserService(session)
    
    user = await user_service.get_or_create_user(callback.from_user.id, "", "")
    removed = await user_service.remove_from_watchlist(user.id, movie_id)
    
    if removed:
        await callback.answer("❌ Watchlist'dan o'chirildi.")
        # Ro'yxatni yangilash yoki xabarni tahrirlash kodi bo'lishi mumkin
    else:
        await callback.answer("Topilmadi.")
