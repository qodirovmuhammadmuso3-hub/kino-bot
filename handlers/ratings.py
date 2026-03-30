from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from services.movie_service import MovieService
from services.user_service import UserService
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import Movie

router = Router()

class CommentStates(StatesGroup):
    waiting_for_comment = State()

@router.callback_query(F.data.startswith("rate_movie:"))
async def rate_movie_handler(callback: types.CallbackQuery):
    movie_id = callback.data.split(":")[1]
    
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.button(text="⭐" * i, callback_data=f"set_rate:{movie_id}:{i}")
    
    builder.adjust(1)
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    await callback.answer("Baho tanlang")

@router.callback_query(F.data.startswith("set_rate:"))
async def set_rate_handler(callback: types.CallbackQuery, session: AsyncSession):
    parts = callback.data.split(":")
    movie_id = int(parts[1])
    stars = int(parts[2])
    
    movie_service = MovieService(session)
    user_service = UserService(session)
    user = await user_service.get_or_create_user(callback.from_user.id, "", "")
    
    await movie_service.add_rating(user.id, movie_id, stars)
    await callback.answer(f"✅ Rahmat! Bahongiz qabul qilindi: {stars} yulduz", show_alert=True)
    
    # Kinoni qaytadan ko'rsatish
    from .movies import send_movie_view
    movie = await session.get(Movie, movie_id)
    if movie:
        await callback.message.delete()
        await send_movie_view(callback.message, movie, session)

@router.callback_query(F.data.startswith("view_comments:"))
async def view_comments_handler(callback: types.CallbackQuery, session: AsyncSession):
    movie_id = int(callback.data.split(":")[1])
    movie_service = MovieService(session)
    
    comments = await movie_service.get_approved_comments(movie_id)
    text = "💬 <b>Sharhlar:</b>\n\n"
    if not comments:
        text += "Hali sharhlar yo'q. Birinchilardan bo'lib yozing!"
    else:
        for c in comments:
            text += f"👤 <b>{c.user.full_name}:</b> {c.text}\n\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✍️ Sharh qoldirish", callback_data=f"add_comment:{movie_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"view_movie_id:{movie_id}")
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("add_comment:"))
async def add_comment_prompt(callback: types.CallbackQuery, state: FSMContext):
    movie_id = callback.data.split(":")[1]
    await state.update_data(movie_id=movie_id)
    await state.set_state(CommentStates.waiting_for_comment)
    await callback.message.answer("✍️ Kinoga o'z fikringizni yozib yuboring (fuhsh yoki reklama taqiqlanadi):")
    await callback.answer()

@router.message(CommentStates.waiting_for_comment)
async def get_comment_handler(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    movie_id = int(data['movie_id'])
    text = message.text.strip()
    
    if len(text) < 5:
        await message.answer("⚠️ Sharh juda qisqa. Kamida 5 ta harf bo'lsin.")
        return
        
    movie_service = MovieService(session)
    user_service = UserService(session)
    user = await user_service.get_or_create_user(message.from_user.id, "", "")
    
    await movie_service.add_comment(user.id, movie_id, text)
    await message.answer("✅ Rahmat! Sharhingiz moderationdan so'ng e'lon qilinadi.")
    await state.clear()
