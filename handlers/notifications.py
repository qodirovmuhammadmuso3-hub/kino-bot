from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from services.movie_service import MovieService
from services.user_service import UserService

router = Router()

@router.callback_query(F.data.startswith("sub_series:"))
async def subscribe_series_handler(callback: types.CallbackQuery, session: AsyncSession):
    movie_id = int(callback.data.split(":")[1])
    movie_service = MovieService(session)
    user_service = UserService(session)
    
    user = await user_service.get_or_create_user(callback.from_user.id, "", "")
    subscribed = await movie_service.subscribe_to_series(user.id, movie_id)
    
    if subscribed:
        await callback.answer("✅ Siz ushbu seryalga obuna bo'ldingiz! Yangi qismlar chiqsa xabar beramiz.", show_alert=True)
    else:
        await callback.answer("⚠️ Siz allaqachon obuna bo'lgansiz.", show_alert=False)
