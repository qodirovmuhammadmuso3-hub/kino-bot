from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from services.movie_service import MovieService
from services.user_service import UserService
from keyboards.pagination import get_pagination_keyboard
from database.models import Movie, Episode
from keyboards.categories import get_categories_keyboard, get_genres_keyboard, get_years_keyboard, get_langs_keyboard
import logging

router = Router()

class MovieStates(StatesGroup):
    waiting_for_query = State()

def get_movie_text(movie):
    # Agar kanal postidan olingan tavsif bo'lsa, uni ishlatamiz
    if movie.description and "┝" in movie.description:
        return f"{movie.description}\n\n🆔 <b>Kodi:</b> <code>{movie.code}</code>"
        
    rating_stars = "⭐" * int(movie.average_rating) if movie.average_rating > 0 else "Noma'lum"
    description = movie.description or "Yo'q"
    text = (
        f"<b>🎬 Nomi:</b> {movie.title}\n"
        f"<b>🆔 Kodi:</b> <code>{movie.code}</code>\n"
        f"<b>📅 Yili:</b> {movie.year}\n"
        f"<b>🎭 Janri:</b> {movie.genre}\n"
        f"<b>🌍 Tili:</b> {movie.lang.upper()}\n"
        f"<b>⭐ Reyting:</b> {movie.average_rating:.1f} ({rating_stars})\n"
        f"<b>👁 Ko'rishlar:</b> {movie.view_count}\n\n"
        f"<b>📝 Tavsif:</b> {description}"
    )
    return text

@router.message(F.text == "🔍 Kino qidirish")
async def start_search(message: types.Message, state: FSMContext):
    await state.set_state(MovieStates.waiting_for_query)
    await message.answer("🔍 Qidirilayotgan kino nomi yoki kodini yuboring:")

@router.message(MovieStates.waiting_for_query)
async def search_handler(message: types.Message, state: FSMContext, session: AsyncSession):
    query = message.text.strip()
    await process_movie_search(query, message, state, session)



@router.message(F.text.regexp(r'(?i)^((kod|id|🆔|🆔 kodi|#)[\s:]*)?\d+$'))
async def direct_code_handler(message: types.Message, session: AsyncSession):
    """Kod orqali to'g'ridan-to'g'ri qidirish (regex: #123, kod: 123, 123)."""
    query = message.text.strip()
    import re
    clean_query = re.sub(r'(?i)^(kod|id|🆔|🆔 kodi|#)[\s:]*', '', query)
    await process_movie_search(clean_query, message, None, session)

@router.message(F.text == "🔥 Yangi kinolar")
async def new_movies_handler(message: types.Message, session: AsyncSession):
    movie_service = MovieService(session)
    results = await movie_service.get_latest_movies(limit=10)
    if results:
        await send_movie_list(message, "🔥 <b>Oxirgi qo'shilgan kinolar:</b>", results)
    else:
        await message.answer("Kinolar topilmadi.")

@router.message(F.text == "⭐️ Top kinolar")
async def top_movies_handler(message: types.Message, session: AsyncSession):
    movie_service = MovieService(session)
    results = await movie_service.get_top_movies(limit=10)
    if results:
        await send_movie_list(message, "⭐️ <b>Eng ko'p ko'rilgan kinolar:</b>", results)
    else:
        await message.answer("Kinolar topilmadi.")

async def send_movie_list(message: types.Message, title: str, results):
    text = f"{title}\n\n"
    builder = InlineKeyboardBuilder()
    for i, m in enumerate(results, 1):
        text += f"{i}. {m.title} (<code>{m.code}</code>)\n"
        builder.button(text=f"{i}", callback_data=f"view_movie:{m.code}")
    
    builder.adjust(5)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

# Bo'limlar handlerlari filters.py fayliga ko'chirildi (dublikatni yo'qotish uchun)

async def process_movie_search(query: str, message: types.Message, state: FSMContext | None, session: AsyncSession, content_type=None):
    movie_service = MovieService(session)
    
    # 1. Kod bo'yicha qidirish
    movie = await movie_service.get_movie_by_code(query)
    if movie:
        await send_movie_view(message, movie, session)
        if state: await state.clear()
        return

    # 2. Nom bo'yicha qidirish
    results = await movie_service.search_movies(query, limit=10, offset=0)
        
    if not results:
        # Agar so'rov kodga o'xshasa (faqat raqam) yoki state bo'lsa javob beramiz
        if state or query.isdigit():
            await message.answer("😔 Uzr, bunday kino topilmadi.")
        return

    # Paginatsiyali ro'yxat
    text = f"🔍 <b>'{query}' bo'yicha natijalar:</b>\n\n"
    builder = InlineKeyboardBuilder()
    for i, m in enumerate(results, 1):
        text += f"{i}. {m.title} (<code>{m.code}</code>)\n"
        builder.button(text=f"{i}", callback_data=f"view_movie:{m.code}")
    
    builder.adjust(5)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

async def send_movie_view(message: types.Message, movie, session: AsyncSession):
    movie_service = MovieService(session)
    user_service = UserService(session)
    
    # Statistikani oshirish va tarixga qo'shish
    movie.view_count += 1
    user = await user_service.get_or_create_user(message.from_user.id, "", "")
    await user_service.add_history(user.id, movie.id)
    await session.commit()

    text = get_movie_text(movie)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📌 Watchlist (Saqlash)", callback_data=f"add_watchlist:{movie.id}")
    builder.button(text="⭐ Baholash", callback_data=f"rate_movie:{movie.id}")
    builder.button(text="💬 Sharhlar", callback_data=f"view_comments:{movie.id}")
    
    if movie.is_series:
        builder.button(text="📺 Barcha qismlar", callback_data=f"view_episodes:{movie.id}:0")
        builder.button(text="🔔 Obuna bo'lish", callback_data=f"sub_series:{movie.id}")

    builder.adjust(1)
    
    # "Bizning kanal" tugmasini qo'shish
    try:
        from services.setting_service import SettingService
        import os
        setting_service = SettingService(session)
        t_raw = await setting_service.get_setting("trailer_channel", os.getenv("TRAILER_CHANNEL", ""))
        if t_raw and "|" in t_raw:
            trailer_link = t_raw.split("|")[1].strip()
            builder.row(types.InlineKeyboardButton(text="🎞 Bizning kanal", url=trailer_link))
    except Exception as e:
        logging.error(f"Trailer link qo'shishda xato: {e}")
    
    if movie.media_type == "photo":
        await message.answer_photo(movie.file_id, caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
    elif movie.media_type == "document":
        await message.answer_document(movie.file_id, caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await message.answer_video(movie.file_id, caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")

# --- Callback Handlers ---

@router.callback_query(F.data.startswith("view_movie:"))
async def process_view_movie_callback(callback: types.CallbackQuery, session: AsyncSession):
    code = callback.data.split(":")[1]
    movie_service = MovieService(session)
    movie = await movie_service.get_movie_by_code(code)
    
    if movie:
        await send_movie_view(callback.message, movie, session)
        await callback.answer()
    else:
        await callback.answer("😔 Uzr, kino topilmadi.", show_alert=True)

@router.callback_query(F.data.startswith("view_movie_id:"))
async def process_view_movie_id_callback(callback: types.CallbackQuery, session: AsyncSession):
    movie_id = int(callback.data.split(":")[1])
    movie = await session.get(Movie, movie_id)
    
    if movie:
        await send_movie_view(callback.message, movie, session)
        await callback.answer()
    else:
        await callback.answer("😔 Uzr, kino topilmadi.", show_alert=True)

@router.callback_query(F.data.startswith("view_episodes:"))
async def view_episodes_handler(callback: types.CallbackQuery, session: AsyncSession):
    parts = callback.data.split(":")
    movie_id = int(parts[1])
    offset = int(parts[2])
    
    movie_service = MovieService(session)
    episodes = await movie_service.get_episodes(movie_id)
    
    if not episodes:
        await callback.answer("⚠️ Hali qismlar qo'shilmagan.", show_alert=True)
        return
        
    text = "📺 <b>Barcha qismlar:</b>\n\n"
    builder = InlineKeyboardBuilder()
    for e in episodes:
        builder.button(text=f"{e.episode_number}-qism", callback_data=f"play_ep:{e.id}")
        
    builder.button(text="🔙 Orqaga", callback_data=f"view_movie_id:{movie_id}")
    builder.adjust(2)
    
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("sub_series:"))
async def subscribe_series(callback: types.CallbackQuery, session: AsyncSession):
    movie_id = int(callback.data.split(":")[1])
    movie_service = MovieService(session)
    user_service = UserService(session)
    
    user = await user_service.get_or_create_user(callback.from_user.id, "", "")
    subscribed = await movie_service.subscribe_to_series(user.id, movie_id)
    
    if subscribed:
        await callback.answer("🔔 Siz yangi qismlarga obuna bo'ldingiz!", show_alert=True)
    else:
        await callback.answer("⚠️ Siz allaqachon obuna bo'lgansiz.")

@router.callback_query(F.data.startswith("play_ep:"))
async def play_episode_callback(callback: types.CallbackQuery, session: AsyncSession):
    ep_id = int(callback.data.split(":")[1])
    episode = await session.get(Episode, ep_id)
    
    if episode:
        await callback.message.answer_video(episode.file_id, caption=f"🎬 {episode.episode_number}-qism")
        await callback.answer()
    else:
        await callback.answer("😔 Uzr, qism topilmadi.", show_alert=True)

@router.message(F.text)
async def universal_search_handler(message: types.Message, state: FSMContext, session: AsyncSession):
    """Barcha matnli xabarlarni qidiruv so'rovi deb hisoblash (Universal Search)."""
    if message.text.startswith('/'): return
    query = message.text.strip()
    # 1 xonali raqamli kodlarni ham qidirishga ruxsat beramiz
    if len(query) < 2 and not query.isdigit(): return
    await process_movie_search(query, message, state, session)
