from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_subscription_kb(channels):
    kb_list = []
    for ch in channels:
        # ch endi lug'at: {"id": "...", "link": "..."}
        kb_list.append([InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=ch["link"])])
    
    kb_list.append([InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=kb_list)
