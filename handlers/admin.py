from aiogram import Router, types, F
# CommandStart import qilindi
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
from database.models import AdChannel, SupportTicket, User
import os
import asyncio
import logging
from aiogram.filters import Command, CommandStart

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

    # Reklama
    waiting_for_broadcast_message = State()
    confirm_broadcast = State()

    # Murojaatga javob
    waiting_for_reply_text = State()

@router.message(CommandStart())
async def start_cmd_handler(message: types.Message, state: FSMContext, session: AsyncSession):
    """/start buyrug'i kelganda state'ni tozalash va start_handler'ga o'tkazish."""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        logging.info(f"FSM State tozalandi (/start): {current_state}")
    
    from handlers.meta import start_handler
    return await start_handler(message, session)

@router.message(Command("admin"))
async def admin_panel(message: types.Message, state: FSMContext, session: AsyncSession):
    user_service = UserService(session)
    if not await user_service.is_admin(message.from_user.id):
        return
    await state.clear() # Har safar kirganda state tozalanadi
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

@router.message(F.text == "🗑 Kinoni o'chirish")
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

@router.message(F.text == "👤 Adminlar")
async def list_admins_handler(message: types.Message, session: AsyncSession):
    user_service = UserService(session)
    if not await user_service.is_admin(message.from_user.id): return
    
    admins = await user_service.get_all_admins()
    text = "<b>👤 Bot adminlari ro'yxati:</b>\n\n"
    
    builder = InlineKeyboardBuilder()
    for i, admin in enumerate(admins, 1):
        admin_name = admin.full_name or "Noma'lum"
        if admin.username:
            admin_name += f" (@{admin.username})"
        
        is_super = admin.user_id == ADMIN_ID
        text += f"{i}. {admin_name} (<code>{admin.user_id}</code>){' 👑' if is_super else ''}\n"
        
        if not is_super and message.from_user.id == ADMIN_ID:
            builder.button(text=f"🗑 {admin_name}", callback_data=f"remove_admin:{admin.user_id}")
    
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("remove_admin:"))
async def process_remove_admin(callback: types.CallbackQuery, session: AsyncSession):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⚠️ Faqat asosiy admin boshqa adminlarni o'chira oladi.", show_alert=True)
        return
    
    target_id = int(callback.data.split(":")[1])
    user_service = UserService(session)
    success = await user_service.set_admin(target_id, False)
    
    await callback.answer()

# --- Kontent Qo'shish ---

@router.message(F.text == "🎬 Kino qo'shish")
async def add_content_start(message: types.Message, state: FSMContext, session: AsyncSession):
    user_service = UserService(session)
    if not await user_service.is_admin(message.from_user.id): return
    
    await state.update_data(content_type="movie")
    await state.set_state(AdminStates.waiting_for_title)
    await message.answer("🎥 Kino <b>nomini</b> kiriting:", parse_mode="HTML")

# add_type: Callback removed as we skip the choice

@router.message(AdminStates.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(title=message.text.strip())
    movie_service = MovieService(session)
    data = await state.get_data()
    next_code = await movie_service.get_next_movie_code(data['content_type'])
    
    await state.set_state(AdminStates.waiting_for_code)
    await message.answer(f"🔢 Kontent <b>kodini</b> kiriting (Tavsiya etiladi: <code>{next_code}</code>):", parse_mode="HTML")

@router.message(AdminStates.waiting_for_code)
async def process_code(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text.strip())
    await state.set_state(AdminStates.waiting_for_file)
    await message.answer("🎞 Kino <b>faylini</b> (video yoki rasm) yuboring:", parse_mode="HTML")

@router.message(F.text == "🔙 Foydalanuvchi menyusi")
async def back_to_user(message: types.Message, state: FSMContext, session: AsyncSession):
    """Asosiy menyuga qaytish va barcha statelarni tozalash (FSM)."""
    from keyboards.general import get_main_menu
    await state.clear()
    await message.answer("🏠 Asosiy menyudasiz.", reply_markup=get_main_menu())

@router.message(AdminStates.waiting_for_file)
async def process_file(message: types.Message, state: FSMContext, session: AsyncSession):
    """Faylni qabul qilish (video, rasm, hujjat or GIF)."""
    # Buyruq yoki orqaga tugmasini tekshirish
    if message.text and (message.text.startswith("/") or message.text == "🔙 Foydalanuvchi menyusi"):
        await state.clear()
        if message.text == "/start":
            from handlers.meta import start_handler
            return await start_handler(message, session)
        from keyboards.general import get_main_menu
        return await message.answer("🏠 Asosiy menyudasiz.", reply_markup=get_main_menu())

    data = await state.get_data()
    file_id = ""
    media_type = "video"
    
    if message.video:
        file_id = message.video.file_id
        media_type = "video"
    elif message.photo:
        file_id = message.photo[-1].file_id
        media_type = "photo"
    elif message.document:
        file_id = message.document.file_id
        media_type = "document"
    elif message.animation:
        file_id = message.animation.file_id
        media_type = "video"
    else:
        await message.answer("⚠️ Iltimos, video, rasm yoki hujjat yuboring.")
        return

    movie_service = MovieService(session)
    new_movie = await movie_service.add_movie(
        title=data['title'],
        code=data['code'],
        content_type=data['content_type'],
        file_id=file_id,
        media_type=media_type
    )
    
    await message.answer(f"✅ Kino muvaffaqiyatli qo'shildi!\nID: {new_movie.id}, Kod: {new_movie.code}")
    await state.clear()

# --- Kontent Tahrirlash ---

@router.message(F.text == "🛠 Kinoni tahrirlash")
async def edit_content_start(message: types.Message, state: FSMContext, session: AsyncSession):
    user_service = UserService(session)
    if not await user_service.is_admin(message.from_user.id): return
    await state.set_state(AdminStates.waiting_for_edit_code)
    await message.answer("📝 Tahrirlanadigan kinoning <b>kodini</b> yuboring:", parse_mode="HTML")

@router.message(AdminStates.waiting_for_edit_code)
async def process_edit_code(message: types.Message, state: FSMContext, session: AsyncSession):
    code = message.text.strip()
    movie_service = MovieService(session)
    movie = await movie_service.get_movie_by_code(code)
    
    if not movie:
        await message.answer(f"❌ '{code}' kodli kino topilmadi.")
        await state.clear()
        return

    await state.update_data(edit_movie_id=movie.id)
    builder = InlineKeyboardBuilder()
    builder.button(text="Nomi", callback_data="edit_field:title")
    builder.button(text="Janri", callback_data="edit_field:genre")
    builder.button(text="Yili", callback_data="edit_field:year")
    builder.button(text="Tavsifi", callback_data="edit_field:description")
    builder.button(text="🗑 O'chirish", callback_data=f"delete_content_init:{movie.id}")
    builder.adjust(2)
    
    await message.answer(f"🎬 <b>{movie.title}</b>\nNimani o'zgartirmoqchisiz?", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("edit_field:"))
async def process_edit_field(callback: types.CallbackQuery, state: FSMContext):
    field = callback.data.split(":")[1]
    await state.update_data(edit_field=field)
    await state.set_state(AdminStates.waiting_for_new_value)
    await callback.message.edit_text(f"✍️ Yangi <b>{field}</b> qiymatini yuboring:", parse_mode="HTML")
    await callback.answer()

@router.message(AdminStates.waiting_for_new_value)
async def save_edit_value(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    movie_id = data['edit_movie_id']
    field = data['edit_field']
    val = message.text.strip()
    
    movie_service = MovieService(session)
    await movie_service.update_movie(movie_id, **{field: val})
    
    await message.answer(f"✅ Ma'lumot yangilandi: <b>{field}</b>", parse_mode="HTML")
    await state.clear()

# --- Kontentni O'chirish (Edit Menyudan) ---

@router.callback_query(F.data.startswith("delete_content_init:"))
async def delete_content_init(callback: types.CallbackQuery, session: AsyncSession):
    movie_id = int(callback.data.split(":")[1])
    movie = await session.get(Movie, movie_id)
    if not movie:
        await callback.answer("❌ Kino topilmadi.")
        return
        
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, o'chirish", callback_data=f"delete_content_final:{movie_id}")
    builder.button(text="❌ Yo'q, bekor qilish", callback_data=f"cancel_edit")
    builder.adjust(1)
    
    await callback.message.edit_text(
        f"❓ <b>{movie.title}</b> (Kod: {movie.code}) ni o'chirishni tasdiqlaysizmi?",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("delete_content_final:"))
async def delete_content_final(callback: types.CallbackQuery, session: AsyncSession):
    movie_id = int(callback.data.split(":")[1])
    movie = await session.get(Movie, movie_id)
    
    if movie:
        code = movie.code
        await session.delete(movie)
        await session.commit()
        await callback.message.edit_text(f"✅ Kino muvaffaqiyatli o'chirildi (Kod: {code}).")
    else:
        await callback.message.edit_text("❌ Kino allaqachon o'chirilgan yoki topilmadi.")
    
    await callback.answer()

# --- Reklama Yuborish ---

@router.message(F.text == "📢 Reklama yuborish")
async def broadcast_start(message: types.Message, state: FSMContext, session: AsyncSession):
    user_service = UserService(session)
    if not await user_service.is_admin(message.from_user.id): return
    await state.set_state(AdminStates.waiting_for_broadcast_message)
    await message.answer("📢 Reklama xabarini yuboring (rasm, video, matn bo'lishi mumkin):")

@router.message(AdminStates.waiting_for_broadcast_message)
async def confirm_broadcast(message: types.Message, state: FSMContext):
    await state.update_data(broadcast_msg_id=message.message_id)
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data="broadcast_confirm:yes")
    builder.button(text="❌ Bekor qilish", callback_data="broadcast_confirm:no")
    await message.answer("Ushbu xabarni hamma foydalanuvchilarga yuborishni tasdiqlaysizmi?", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("broadcast_confirm:"))
async def process_broadcast(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    confirm = callback.data.split(":")[1]
    if confirm == "no":
        await callback.message.edit_text("❌ Reklama bekor qilindi.")
        await state.clear()
        return

    data = await state.get_data()
    msg_id = data['broadcast_msg_id']
    user_service = UserService(session)
    user_ids = await user_service.get_all_user_ids()
    
    await callback.message.edit_text(f"⏳ Reklama {len(user_ids)} kishiga yuborish boshlandi...")
    
    count = 0
    for uid in user_ids:
        try:
            await callback.bot.copy_message(chat_id=uid, from_chat_id=callback.from_user.id, message_id=msg_id)
            count += 1
            await asyncio.sleep(0.05) # Flood control
        except:
            continue
            
    await callback.message.answer(f"✅ Reklama {count} kishiga muvaffaqiyatli yuborildi.")
    await state.clear()

# --- Statistika Callbacks ---

@router.callback_query(F.data == "stats_hourly")
async def hourly_stats(callback: types.CallbackQuery, session: AsyncSession):
    stats_service = StatsService(session)
    data = await stats_service.get_hourly_activity()
    text = "<b>🕒 Oxirgi 24 soatlik faollik:</b>\n\n"
    if not data:
        text += "Ma'lumot yo'q."
    else:
        for row in data:
            # PostgreSQL da row ob'ekt, SQLite da tuple bo'lishi mumkin
            h, c = (row.hour, row.count) if hasattr(row, 'hour') else (row[0], row[1])
            text += f"⏰ {int(h):02d}:00 — {c} marta\n"
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "stats_weekly_top")
async def weekly_top_stats(callback: types.CallbackQuery, session: AsyncSession):
    stats_service = StatsService(session)
    movies = await stats_service.get_weekly_top_movies()
    text = "<b>📅 Haftalik TOP-5 kinolar:</b>\n\n"
    if not movies:
        text += "Ma'lumot yo'q."
    else:
        for i, m in enumerate(movies, 1):
            # SQLAlchemy result row handling
            movie = m[0]
            views = m[1]
            text += f"{i}. {movie.title} — {views} marta\n"
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

# --- Orqaga ---

# Handler yuqoriga ko'chirildi (priority uchun)

# --- Kanallar Sozlamalari ---

@router.message(F.text == "📣 Kanallar")
async def channels_settings(message: types.Message, session: AsyncSession):
    user_service = UserService(session)
    if not await user_service.is_admin(message.from_user.id): return
    setting_service = SettingService(session)
    trailer = await setting_service.get_setting("trailer_channel", "Sozlanmagan")
    movie = await setting_service.get_setting("movie_channel", "Sozlanmagan")
    
    text = (
        "<b>📣 Kanal sozlamalari:</b>\n\n"
        f"🎬 <b>Kino:</b> <code>{movie}</code>\n"
        f"🎞 <b>Treyler:</b> <code>{trailer}</code>\n\n"
        "O'zgartirmoqchi bo'lgan kanalni tanlang:"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🎬 Kino kanali", callback_data="set_ch:movie_channel")
    builder.button(text="🎞 Treyler kanali", callback_data="set_ch:trailer_channel")
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("set_ch:"))
async def process_set_channel(callback: types.CallbackQuery, state: FSMContext):
    channel_key = callback.data.split(":")[1]
    await state.update_data(channel_key=channel_key)
    await state.set_state(AdminStates.waiting_for_channel_value)
    
    names = {"movie_channel": "🎬 Kino kanali", "trailer_channel": "🎞 Treyler kanali"}
    
    text = (
        f"✍️ <b>{names[channel_key]}</b> uchun yangi qiymatni kiriting.\n\n"
        "💡 <b>ID-ni qanday olish mumkin?</b>\n"
        "1. Kanalizdan xabarni @userinfobot-ga yuboring.\n"
        "2. Yoki uning @username'ini kiriting.\n\n"
        "<b>Format:</b> <code>ID|LINK</code> yoki <code>@username|LINK</code>"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Sozlamani o'chirish", callback_data=f"clear_ch:{channel_key}")
    builder.button(text="❌ Bekor qilish", callback_data="cancel_edit")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("clear_ch:"))
async def clear_channel_setting(callback: types.CallbackQuery, session: AsyncSession):
    key = callback.data.split(":")[1]
    setting_service = SettingService(session)
    await setting_service.set_setting(key, "")
    await callback.message.edit_text(f"✅ <b>{key}</b> sozlamasi muvaffaqiyatli tozalandi.", parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "cancel_edit")
async def cancel_edit(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Tahrirlash bekor qilindi.")
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
    text = (
        "🆔 Kanal <b>ID</b> sini yuboring (-100...) yoki uning <b>@username</b>ini.\n\n"
        "💡 ID-ni olish uchun kanaldan xabarni @userinfobot-ga yuboring."
    )
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

@router.message(AdminStates.waiting_for_ad_channel_id)
async def process_ad_channel_id(message: types.Message, state: FSMContext):
    ch_id_str = message.text.strip()
    # ID yoki @username ekanligini tekshirish
    if not (ch_id_str.startswith("-100") or ch_id_str.startswith("@")):
        await message.answer("⚠️ Iltimos, kanal ID'sini (-100- bilan boshlanadigan) yoki @username'ini yuboring.")
        return
        
    await state.update_data(ad_channel_id=ch_id_str)
    await state.set_state(AdminStates.waiting_for_ad_channel_link)
    await message.answer("🔗 Kanal <b>linkini</b> yuboring (https://t.me/...):", parse_mode="HTML")

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

# --- Murojaatlar ---

@router.message(F.text == "📨 Murojaatlar")
async def list_tickets(message: types.Message, session: AsyncSession):
    user_service = UserService(session)
    if not await user_service.is_admin(message.from_user.id): return
    
    stmt = select(SupportTicket).where(SupportTicket.status == "open").order_by(SupportTicket.created_at.desc())
    res = await session.execute(stmt)
    tickets = res.scalars().all()
    
    if not tickets:
        await message.answer("✅ Hozircha yangi murojaatlar yo'q.")
        return
        
    for t in tickets:
        builder = InlineKeyboardBuilder()
        builder.button(text="✍️ Javob berish", callback_data=f"reply_ticket:{t.id}")
        builder.button(text="❌ Yopish", callback_data=f"close_ticket:{t.id}")
        builder.adjust(2)
        
        await message.answer(
            f"📨 <b>Murojaat #{t.id}</b>\nKimdan: <code>{t.user_id}</code>\n\n<b>Xabar:</b> {t.message}",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("reply_ticket:"))
async def reply_ticket_start(callback: types.CallbackQuery, state: FSMContext):
    ticket_id = int(callback.data.split(":")[1])
    await state.update_data(reply_ticket_id=ticket_id)
    await state.set_state(AdminStates.waiting_for_reply_text)
    await callback.message.answer(f"✍️ <b>#{ticket_id}</b>-murojaat uchun javobingizni yozing:", parse_mode="HTML")
    await callback.answer()

@router.message(AdminStates.waiting_for_reply_text)
async def process_reply_text(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    ticket_id = data['reply_ticket_id']
    text = message.text.strip()
    
    ticket = await session.get(SupportTicket, ticket_id)
    if ticket:
        ticket.answer = text
        ticket.status = "closed"
        await session.commit()
        
        # Foydalanuvchiga yuborish
        try:
            await message.bot.send_message(
                ticket.user_id,
                f"📨 <b>Admin murojaatingizga javob berdi!</b>\n\n<b>Sizning xabaringiz:</b> {ticket.message}\n\n<b>Admin javobi:</b> {text}",
                parse_mode="HTML"
            )
            await message.answer(f"✅ Javob yuborildi (Ticket #{ticket_id})")
        except Exception as e:
            await message.answer(f"❌ Foydalanuvchiga yuborishda xato: {e}")
            
    await state.clear()

@router.callback_query(F.data.startswith("close_ticket:"))
async def close_ticket(callback: types.CallbackQuery, session: AsyncSession):
    ticket_id = int(callback.data.split(":")[1])
    ticket = await session.get(SupportTicket, ticket_id)
    if ticket:
        ticket.status = "closed"
        await session.commit()
        await callback.message.edit_text(f"❌ Murojaat #{ticket_id} yopildi.")
    await callback.answer()
