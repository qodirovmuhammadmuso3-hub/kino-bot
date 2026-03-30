from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def get_pagination_keyboard(items, page: int, total_pages: int, callback_prefix: str):
    builder = InlineKeyboardBuilder()
    
    # Navigatsiya tugmalari
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"{callback_prefix}:page:{page-1}"))
    
    nav_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="ignore"))
    
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"{callback_prefix}:page:{page+1}"))
    
    if nav_row:
        builder.row(*nav_row)
        
    return builder.as_markup()
