from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    """Asosiy menyu klaviaturasini qaytaradi."""
    kb = [
        [KeyboardButton(text="🔍 Kino qidirish"), KeyboardButton(text="🔍 Anime qidirish")],
        [KeyboardButton(text="🔥 Yangi kinolar"), KeyboardButton(text="⭐️ Top kinolar")],
        [KeyboardButton(text="📂 Bo'limlar"), KeyboardButton(text="🆘 Yordam")],
        [KeyboardButton(text="👨‍💻 Adminga murojaat")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_categories_kb():
    """Bo'limlar tanlash uchun inline klaviatura."""
    kb = [
        [InlineKeyboardButton(text="🎭 Janrlar bo'yicha", callback_data="cat:genres")],
        [InlineKeyboardButton(text="📅 Yillar bo'yicha", callback_data="cat:years")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_items_kb(items, prefix, current_page=0):
    """Janrlar yoki yillar ro'yxatini inline klaviaturada qaytaradi."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    for item in items:
        builder.button(text=str(item), callback_data=f"{prefix}:{item}")
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="cat:back"))
    return builder.as_markup()
