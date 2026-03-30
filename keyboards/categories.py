from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types

def get_categories_keyboard():
    builder = InlineKeyboardBuilder()
    
    # Janrlar
    builder.button(text="🎭 Janrlar", callback_data="show_genres")
    # Yillar
    builder.button(text="📅 Yillar", callback_data="show_years")
    # Tillar
    builder.button(text="🌍 Tillar", callback_data="show_langs")
    
    builder.adjust(2)
    return builder.as_markup()

def get_genres_keyboard(genres):
    builder = InlineKeyboardBuilder()
    for g in genres:
        builder.button(text=g, callback_data=f"filter_genre:{g}")
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_categories"))
    return builder.as_markup()

def get_years_keyboard():
    builder = InlineKeyboardBuilder()
    import datetime
    current_year = datetime.datetime.now().year
    for y in range(current_year, current_year - 10, -1):
        builder.button(text=str(y), callback_data=f"filter_year:{y}")
    builder.adjust(3)
    builder.row(types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_categories"))
    return builder.as_markup()

def get_langs_keyboard():
    builder = InlineKeyboardBuilder()
    langs = {"uz": "🇺🇿 O'zbekcha", "ru": "🇷🇺 Ruscha", "en": "🇺🇸 Inglizcha"}
    for code, name in langs.items():
        builder.button(text=name, callback_data=f"filter_lang:{code}")
    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_categories"))
    return builder.as_markup()
