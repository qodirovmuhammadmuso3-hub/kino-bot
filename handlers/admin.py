from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from services.stats_service import StatsService
from services.movie_service import MovieService
from services.user_service import UserService
from keyboards.admin import get_admin_menu, get_stats_keyboard
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.setting_service import SettingService
from database.models import AdChannel
import os

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

class AdminStates(StatesGroup):
    waiting_for_new_admin_id = State()
    waiting_for_movie_code_to_delete = State()
    
    # Kontent qo'shish
    waiting_for_content_type = State() # movie or series
    waiting_for_title = State()
    waiting_for_code = State()
    waiting_for_file = State()
    
    # Tahrirlash
    waiting_for_edit_code = State()
    waiting_for_edit_field = State()
    waiting_for_new_value = State()
    
    # Kanallar sozlamalari
    waiting_for_channel_choice = State()
    waiting_for_channel_value = State()

    # Majburiy kanallar
    waiting_for_ad_channel_id = State()
    waiting_for_ad_channel_link = State()

@router.message(Command("admin"))
async def admin_panel(message: types.Message, session: AsyncSession):
    user_service = UserService(session)
    if not await user_service.is_admin(message.from_user.id):
        return
    await message.answer("🛠 <b>Admin Paneliga xush kelibsiz!</b>", reply_markup=get_admin_menu(), parse_mode="HTML")

@router.message(F.text == "📊 Kengaytirilgan statistika")
async def stats_handler(message: types.Message, session: AsyncSession):
    user_service = UserService(session)
    if not await user_service.is_admin(message.from_user.id): return
    stats_service = StatsService(session)
    
    total_users = await stats_service.get_user_growth(365)
    new_users_week = await stats_service.get_user_growth(7)
    top_movies = await stats_service.get_top_10_movies()
    
    text = (
        "<b>📊 Bot statistikasi:</b>\n\n"
        f"👥 Jami foydalanuvchilar: {total_users}\n"
        f"📈 Haftalik yangi: {new_users_week}\n\n"
        "<b>🔝 TOP-10 kinolar:</b>\n"
    )
    for i, m in enumerate(top_movies, 1):
        text += f"{i}. {m.title} — {m.view_count} marta\n"
    await message.answer(text, reply_markup=get_stats_keyboard(), parse_mode="HTML")

@router.message(F.text == "🗑 Kontentni o'chirish")
async def delete_movie_prompt(message: types.Message, state: FSMContext, session: AsyncSession):
    user_service = UserService(session)
    if not await user_service.is_admin(message.from_user.id): return
    await state.set_state(AdminStates.waiting_for_movie_code_to_delete)
    await message.answer("📝 O'chiriladigan kinoning <b>kodini</b> yuboring:", parse_mode="HTML")

@router.message(AdminStates.waiting_for_movie_code_to_delete)
async def process_movie_deletion(message: types.Message, state: FSMContext, session: AsyncSession):
    code = message.text.strip()
    movie_service = MovieService(session)
    deleted = await movie_service.delete_movie(code)
    if deleted:
        await message.answer(f"✅ Kino (kod: {code}) muvaffaqiyatli o'chirildi.")
    else:
        await message.answer(f"❌ Kino topilmadi (kod: {code}).")
    await state.clear()

@router.message(F.text == "➕ Admin qo'shish")
async def add_admin_prompt(message: types.Message, state: FSMContext, session: AsyncSession):
    user_service = UserService(session)
    if message.from_user.id != ADMIN_ID:
        await message.answer("⚠️ Faqat asosiy admin yangi admin qo'sha oladi.")
        return
    await state.set_state(AdminStates.waiting_for_new_admin_id)
    await message.answer("👤 Yangi adminning <b>Telegram ID</b> sini yuboring:", parse_mode="HTML")

@router.message(AdminStates.waiting_for_new_admin_id)
async def process_add_admin(message: types.Message, state: FSMContext, session: AsyncSession):
    try:
        new_admin_id = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ ID faqat raqamlardan iborat bo'lishi kerak.")
        return
    user_service = UserService(session)
    success = await user_service.set_admin(new_admin_id, True)
    if success:
        await message.answer(f"✅ Foydalanuvchi {new_admin_id} admin etib tayinlandi.")
    else:
        await message.answer("❌ Foydalanuvchi topilmadi. Avval u botga kirgan bo'lishi kerak.")
    await state.clear()

# --- Kanallar Sozlamalari ---

@router.message(F.text == "📣 Kanallar")
async def channels_settings(message: types.Message, session: AsyncSession):
    user_service = UserService(session)
    if not await user_service.is_admin(message.from_user.id): return
    setting_service = SettingService(session)
    trailer = await setting_service.get_setting("trailer_channel", "Sozlanmagan")
    anime = await setting_service.get_setting("anime_channel", "Sozlanmagan")
    movie = await setting_service.get_setting("movie_channel", "Sozlanmagan")
    
    text = (
        "<b>📣 Kanal sozlamalari:</b>\n\n"
        f"🎬 <b>Kino:</b> <code>{movie}</code>\n"
        f"📺 <b>Anime:</b> <code>{anime}</code>\n"
        f"🎞 <b>Treyler:</b> <code>{trailer}</code>\n\n"
        "O'zgartirmoqchi bo'lgan kanalni tanlang:"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🎬 Kino kanali", callback_data="set_ch:movie_channel")
    builder.button(text="📺 Anime kanali", callback_data="set_ch:anime_channel")
    builder.button(text="🎞 Treyler kanali", callback_data="set_ch:trailer_channel")
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("set_ch:"))
async def process_set_channel(callback: types.CallbackQuery, state: FSMContext):
    channel_key = callback.data.split(":")[1]
    await state.update_data(channel_key=channel_key)
    await state.set_state(AdminStates.waiting_for_channel_value)
    names = {"movie_channel": "Kino kanali", "anime_channel": "Anime kanali", "trailer_channel": "Treyler kanali"}
    await callback.message.edit_text(f"✍️ <b>{names[channel_key]}</b> uchun yangi qiymatni kiriting.\nFormat: <code>ID|LINK</code>", parse_mode="HTML")
    await callback.answer()

@router.message(AdminStates.waiting_for_channel_value)
async def save_channel_setting(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    key = data['channel_key']
    val = message.text.strip()
    setting_service = SettingService(session)
    await setting_service.set_setting(key, val)
    await message.answer(f"✅ Sozlama saqlandi: <b>{key}</b>", parse_mode="HTML")
    await state.clear()

# --- Majburiy obuna ---

@router.message(F.text == "📢 Majburiy obuna")
async def mandatory_subs_manager(message: types.Message, session: AsyncSession):
    user_service = UserService(session)
    if not await user_service.is_admin(message.from_user.id): return
    
    stmt = select(AdChannel)
    res = await session.execute(stmt)
    channels = res.scalars().all()
    
    text = "<b>📢 Majburiy obuna kanallari:</b>\n\n"
    if not channels:
        text += "Hozircha kanallar yo'q."
    else:
        for i, ch in enumerate(channels, 1):
            text += f"{i}. <code>{ch.channel_id}</code>\n🔗 {ch.link}\n\n"
            
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Kanal qo'shish", callback_data="add_ad_channel")
    if channels:
        builder.button(text="🗑 Kanalni o'chirish", callback_data="del_ad_channel")
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data == "add_ad_channel")
async def add_ad_channel_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_ad_channel_id)
    await callback.message.answer("🆔 Kanal <b>ID</b> sini yuboring (-100...):", parse_mode="HTML")
    await callback.answer()

@router.message(AdminStates.waiting_for_ad_channel_id)
async def process_ad_channel_id(message: types.Message, state: FSMContext):
    try:
        ch_id = int(message.text.strip())
        await state.update_data(ad_channel_id=ch_id)
        await state.set_state(AdminStates.waiting_for_ad_channel_link)
        await message.answer("🔗 Kanal <b>linkini</b> yuboring (https://t.me/...):", parse_mode="HTML")
    except ValueError:
        await message.answer("⚠️ ID faqat raqam bo'lishi kerak.")

@router.message(AdminStates.waiting_for_ad_channel_link)
async def process_ad_channel_link(message: types.Message, state: FSMContext, session: AsyncSession):
    link = message.text.strip()
    data = await state.get_data()
    session.add(AdChannel(channel_id=data['ad_channel_id'], link=link))
    await session.commit()
    await message.answer("✅ Kanal qo'shildi!")
    await state.clear()

@router.callback_query(F.data == "del_ad_channel")
async def del_ad_channel_list(callback: types.CallbackQuery, session: AsyncSession):
    res = await session.execute(select(AdChannel))
    channels = res.scalars().all()
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.button(text=f"🗑 {ch.channel_id}", callback_data=f"del_ad_confirm:{ch.id}")
    builder.adjust(1)
    await callback.message.edit_text("O'chiriladigan kanalni tanlang:", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("del_ad_confirm:"))
async def process_del_confirm(callback: types.CallbackQuery, session: AsyncSession):
    ch_id = int(callback.data.split(":")[1])
    await session.execute(delete(AdChannel).where(AdChannel.id == ch_id))
    await session.commit()
    await callback.message.edit_text("✅ Kanal o'chirildi.")
    await callback.answer()
