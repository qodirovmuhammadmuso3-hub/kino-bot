from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable, Dict, Any, Awaitable
from sqlalchemy import select
from database.models import AdChannel, User
import logging

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        state = data.get("state")
        session = data["session"]
        bot = data["bot"]
        user_id = event.from_user.id

        # Skip admin check for /admin commands
        if isinstance(event, Message) and event.text and event.text.startswith("/admin"):
            return await handler(event, data)
            
        # Adminlarni tekshirmaymiz
        stmt = select(User).where(User.user_id == user_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        if user and user.is_admin:
            return await handler(event, data)

        # Majburiy kanallarni olish
        stmt = select(AdChannel)
        res = await session.execute(stmt)
        channels = res.scalars().all()
        
        if not channels:
            return await handler(event, data)

        not_subscribed = []
        for ch in channels:
            try:
                # String ID'ni int ga o'girish (agar raqam bo'lsa)
                target_id = ch.channel_id
                if target_id.startswith("-100") or target_id.isdigit():
                    target_id = int(target_id)
                
                member = await bot.get_chat_member(target_id, user_id)
                if member.status not in ["member", "administrator", "creator"]:
                    not_subscribed.append(ch)
            except Exception as e:
                logging.warning(f"Obunani tekshirishda xato ({ch.channel_id}): {e}")
                continue
                
        if not_subscribed:
            # Deep link bilan kelgan bo'lsa, kodni saqlab qo'yamiz
            if isinstance(event, Message) and event.text and event.text.startswith("/start "):
                args = event.text.split(" ", 1)[1]
                if state:
                    await state.update_data(pending_movie_code=args)
                    logging.info(f"Deep-link kodi xotiraga saqlandi: {args}")

            text = "<b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling 👇</b>"
            builder = InlineKeyboardBuilder()
            for i, ch in enumerate(not_subscribed, 1):
                builder.button(text=f"{i}-kanalga a'zo bo'lish", url=ch.link)
            
            builder.button(text="✅ Tekshirish", callback_data="check_subs")
            builder.adjust(1)
            
            if isinstance(event, Message):
                await event.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
            else:
                await event.answer("Avval barcha kanallarga obuna bo'ling!", show_alert=True)
                await event.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
            return

        return await handler(event, data)
