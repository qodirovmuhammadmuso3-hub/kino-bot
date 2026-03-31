from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from services.movie_service import MovieService
from keyboards.pagination import get_pagination_keyboard
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.message(F.text == "📂 Bo'limlar")
async def categories_handler(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🎭 Janrlar", callback_data="filter_type:genre")
    builder.button(text="🌍 Tillar", callback_data="filter_type:lang")
    builder.adjust(1)
    await message.answer("📂 Bo'limni tanlang:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("filter_type:"))
async def filter_type_handler(callback: types.CallbackQuery, session: AsyncSession):
    f_type = callback.data.split(":")[1]
    movie_service = MovieService(session)
    
    builder = InlineKeyboardBuilder()
    if f_type == "genre":
        genres = await movie_service.get_genres()
        for g in genres:
            builder.button(text=g, callback_data=f"by_genre:{g}:0")
    else:
        langs = ["uz", "ru", "en"] # Statik tillar
        for l in langs:
            builder.button(text=l.upper(), callback_data=f"by_lang:{l}:0")
            
    builder.adjust(2)
    builder.button(text="🔙 Orqaga", callback_data="back_to_cats")
    await callback.message.edit_text(f"Tanlang:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("by_genre:"))
async def by_genre_handler(callback: types.CallbackQuery, session: AsyncSession):
    parts = callback.data.split(":")
    genre = parts[1]
    page = int(parts[2])
    
    movie_service = MovieService(session)
    movies = await movie_service.get_movies_by_genre(genre, limit=10, offset=page*10)
    
    if not movies:
        await callback.answer("Bu janrda kinolar topilmadi.")
        return
        
    text = f"🎭 <b>Janr: {genre}</b> (Sahifa: {page+1}):\n\n"
    builder = InlineKeyboardBuilder()
    for i, m in enumerate(movies, 1):
        text += f"{i}. {m.title} (<code>{m.code}</code>)\n"
        builder.button(text=f"{i}", callback_data=f"view_movie:{m.code}")
    
    builder.adjust(5)
    # Paginatsiya tugmalarini qo'shish
    # Bu yerda total_pages ni hisoblash kerak (oddiyroq demo uchun 5)
    nav_kb = get_pagination_keyboard(movies, page, 5, f"by_genre:{genre}")
    builder.attach(InlineKeyboardBuilder.from_markup(nav_kb))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data == "back_to_cats")
async def back_to_cats_handler(callback: types.CallbackQuery):
    """Bo'limlar menyusiga qaytish."""
    await categories_handler(callback.message)
    await callback.answer()

@router.callback_query(F.data.startswith("by_lang:"))
async def by_lang_handler(callback: types.CallbackQuery, session: AsyncSession):
    """Til bo'yicha filtrlash."""
    parts = callback.data.split(":")
    lang = parts[1]
    page = int(parts[2])
    
    movie_service = MovieService(session)
    movies = await movie_service.get_movies_by_lang(lang, limit=10, offset=page*10)
    
    if not movies:
        await callback.answer("Bu tilda kinolar topilmadi.")
        return
        
    text = f"🌍 <b>Til: {lang.upper()}</b> (Sahifa: {page+1}):\n\n"
    builder = InlineKeyboardBuilder()
    for i, m in enumerate(movies, 1):
        text += f"{i}. {m.title} (<code>{m.code}</code>)\n"
        builder.button(text=f"{i}", callback_data=f"view_movie:{m.code}")
    
    builder.adjust(5)
    from keyboards.pagination import get_pagination_keyboard
    nav_kb = get_pagination_keyboard(movies, page, 5, f"by_lang:{lang}")
    builder.attach(InlineKeyboardBuilder.from_markup(nav_kb))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
