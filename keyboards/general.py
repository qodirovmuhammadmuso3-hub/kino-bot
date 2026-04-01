from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    kb = [
        [KeyboardButton(text="🔍 Kino qidirish")],
        [KeyboardButton(text="🔥 Yangi kinolar"), KeyboardButton(text="⭐️ Top kinolar")],
        [KeyboardButton(text="📌 Watchlist"), KeyboardButton(text="🕒 Tarix")],
        [KeyboardButton(text="📂 Bo'limlar"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="👨‍💻 Adminga murojaat")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
