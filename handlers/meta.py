from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command, CommandObject
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_service import UserService
from keyboards.general import get_main_menu
import logging

router = Router()

@router.message(CommandStart())
async def start_handler(message: types.Message, session: AsyncSession, command: CommandObject = None):
    user_service = UserService(session)
    user = await user_service.get_or_create_user(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username
    )
    
    # Deep linking (kod bilan kirish)
    if command and command.args:
        from handlers.movies import process_movie_search
        await process_movie_search(command.args, message, None, session)
        return
    
    display_name = message.from_user.mention_html()
    welcome_text = (
        f"👋 <b>Assalomu alaykum, {display_name}!</b>\n\n"
        "Kino va Anime botimizga xush kelibsiz! Bu yerda siz sevimli kinolaringizni "
        "qidirishingiz, reyting berishingiz va Watchlist yaratishingiz mumkin."
    )
    await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode="HTML")

@router.callback_query(F.data == "check_subs")
async def check_subscription_handler(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer("⏳ Tekshirilmoqda...")
    # Middleware yana tekshiradi, agar o'tsa start_handler chaqiriladi
    await start_handler(callback.message, session)
    try: await callback.message.delete()
    except: pass

@router.message(F.text == "📊 Statistika")
async def stats_handler(message: types.Message, session: AsyncSession):
    from services.movie_service import MovieService
    user_service = UserService(session)
    movie_service = MovieService(session)
    
    users_count = await user_service.get_total_users_count()
    movies_count = await movie_service.get_total_movies_count()
    
    text = (
        "📊 <b>Bot statistikasi:</b>\n\n"
        f"👤 <b>Foydalanuvchilar:</b> {users_count}\n"
        f"🎬 <b>Kinolar soni:</b> {movies_count}\n\n"
        "Siz bilan birga o'sayotganimizdan xursandmiz! 😊"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("help"))
async def help_handler(message: types.Message):
    help_text = (
        "<b>Botdan foydalanish bo'yicha yordam:</b>\n\n"
        "🔍 <b>Qidirish:</b> Kino nomini yoki kodini yuboring.\n"
        "📌 <b>Watchlist:</b> 'Keyinroq ko'raman' ro'yxatiga qo'shish uchun kino ostidagi tugmani bosing.\n"
        "⭐ <b>Reyting:</b> Kinolarga 1 dan 5 gacha baho bering.\n"
        "📁 <b>Bo'limlar:</b> Janrlar va yillar bo'yicha filtrlashdan foydalaning."
    )
    await message.answer(help_text, parse_mode="HTML")
