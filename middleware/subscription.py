from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from keyboards.subscription import get_subscription_kb
import database

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        bot = data["bot"]
        
        # Obunani tekshirish
        ad_channels = await database.get_ad_channels()
        for channel in ad_channels:
            try:
                member = await bot.get_chat_member(channel["id"], user_id)
                if member.status not in ["member", "administrator", "creator"]:
                    text = "<b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling 👇</b>"
                    kb = get_subscription_kb(ad_channels)
                    
                    if isinstance(event, Message):
                        await event.answer(text, reply_markup=kb, parse_mode="HTML")
                    elif isinstance(event, CallbackQuery):
                        await event.answer("Avval obuna bo'ling!", show_alert=True)
                        await event.message.answer(text, reply_markup=kb, parse_mode="HTML")
                    return
            except Exception:
                continue
                
        return await handler(event, data)
