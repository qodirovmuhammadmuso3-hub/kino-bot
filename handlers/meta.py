from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import SupportTicket, User
from services.user_service import UserService
from keyboards.general import get_main_menu
import logging
import os

router = Router()

class SupportStates(StatesGroup):
    waiting_for_support_message = State()

@router.message(CommandStart())
async def start_handler(message: types.Message, session: AsyncSession, state: FSMContext = None, command: CommandObject = None):
    user_service = UserService(session)
    user = await user_service.get_or_create_user(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username
    )
    
    # Deep linking (kod bilan kirish)
    args = command.args if command else None
    
    # Agar callback'dan kelayotgan bo'lsak va state'da saqlangan kod bo'lsa
    if not args and state:
        data = await state.get_data()
        args = data.get("pending_movie_code")
        if args:
            await state.update_data(pending_movie_code=None) # Bir marta ishlatamiz
    
    if args:
        from handlers.movies import process_movie_search
        await process_movie_search(args, message, None, session)
        return
    
    display_name = message.from_user.mention_html()
    welcome_text = (
        f"👋 <b>Assalomu alaykum, {display_name}!</b>\n\n"
        "Kino botimizga xush kelibsiz! Bu yerda siz sevimli kinolaringizni "
        "qidirishingiz, reyting berishingiz va Watchlist yaratishingiz mumkin."
    )
    await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode="HTML")

@router.callback_query(F.data == "check_subs")
async def check_subscription_handler(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer("⏳ Tekshirilmoqda...")
    # Middleware yana tekshiradi. Agar o'tsa, start_handler chaqiriladi.
    # Bu yerda start_handler'ga state'ni uzatamiz, u yerdan pending_movie_code olinadi.
    await start_handler(callback.message, session, state)
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

@router.message(F.text == "👨‍💻 Adminga murojaat")
async def support_start(message: types.Message, state: FSMContext):
    await state.set_state(SupportStates.waiting_for_support_message)
    await message.answer("✍️ <b>Adminlar uchun murojaat qoldiring:</b>\n\nMuammo yoki taklifingizni yozib yuboring, adminlarimiz tez orada javob berishadi.", parse_mode="HTML")

@router.message(SupportStates.waiting_for_support_message)
async def process_support_message(message: types.Message, state: FSMContext, session: AsyncSession):
    text = message.text.strip()
    if not text:
        await message.answer("Iltimos, matnli xabar yuboring.")
        return
        
    # Bazaga saqlash
    ticket = SupportTicket(user_id=message.from_user.id, message=text)
    session.add(ticket)
    await session.commit()
    
    await message.answer("✅ <b>Murojaatingiz yuborildi!</b>\nAdminlarimiz javob berishini kuting.", parse_mode="HTML")
    await state.clear()
    
    # Adminlarni xabardor qilish
    ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
    try:
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="Javob berish", callback_data=f"reply_ticket:{ticket.id}")
        await message.bot.send_message(
            ADMIN_ID, 
            f"📨 <b>Yangi murojaat!</b>\nKimdan: {message.from_user.full_name} (ID: {message.from_user.id})\n\n<b>Xabar:</b> {text}",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except:
        pass
