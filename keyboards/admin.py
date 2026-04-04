from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_menu():
    kb = [
        [KeyboardButton(text="🎬 Kino qo'shish"), KeyboardButton(text="🎞 Seryalga qism qo'shish")],
        [KeyboardButton(text="🗑 Kinoni o'chirish"), KeyboardButton(text="🛠 Kinoni tahrirlash")],
        [KeyboardButton(text="➕ Admin qo'shish"), KeyboardButton(text="👤 Adminlar")],
        [KeyboardButton(text="📨 Murojaatlar"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="📣 Kanallar"), KeyboardButton(text="📢 Majburiy obuna")],
        [KeyboardButton(text="📢 Reklama yuborish")],
        [KeyboardButton(text="🔙 Foydalanuvchi menyusi")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_stats_keyboard():
    kb = [
        [InlineKeyboardButton(text="📈 Faollik grafigi (24s)", callback_data="stats_hourly")],
        [InlineKeyboardButton(text="📅 Haftalik TOP", callback_data="stats_weekly_top")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
