from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_menu():
    kb = [
        [KeyboardButton(text="🎬 Kontent qo'shish"), KeyboardButton(text="🗑 Kontentni o'chirish")],
        [KeyboardButton(text="🛠 Kontentni tahrirlash"), KeyboardButton(text="➕ Admin qo'shish")],
        [KeyboardButton(text="👤 Adminlar"), KeyboardButton(text="📨 Murojaatlar")],
        [KeyboardButton(text="📊 Kengaytirilgan statistika"), KeyboardButton(text="📢 Reklama yuborish")],
        [KeyboardButton(text="📣 Kanallar"), KeyboardButton(text="📢 Majburiy obuna")],
        [KeyboardButton(text="🔙 Foydalanuvchi menyusi")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_stats_keyboard():
    kb = [
        [InlineKeyboardButton(text="📈 Faollik grafigi (24s)", callback_data="stats_hourly")],
        [InlineKeyboardButton(text="📅 Haftalik TOP", callback_data="stats_weekly_top")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
