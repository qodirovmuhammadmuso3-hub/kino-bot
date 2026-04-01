import re
import logging
import os
from aiogram import Router, types, Bot
from sqlalchemy.ext.asyncio import AsyncSession
from services.movie_service import MovieService
from services.setting_service import SettingService
from config import ADMIN_ID, parse_channel

router = Router()

def parse_episode(text, raw_title):
    """Matndan qism raqamini va sarlavhani ajratib oladi."""
    is_series = False
    episode_number = None
    title = raw_title
    
    # Masalan: "Naruto 1-qism" yoki "1-qism" yoki "Qism 1"
    ep_match = re.search(r'(\d+)\s*[- ]?qism', text, re.IGNORECASE)
    if ep_match:
        is_series = True
        episode_number = int(ep_match.group(1))
        title = re.sub(r'\d+\s*[- ]?qism.*', '', raw_title, flags=re.IGNORECASE)
        title = title.strip().rstrip('-._ ')
    
    return is_series, episode_number, title

@router.channel_post()
@router.edited_channel_post()
async def sync_movie_handler(post: types.Message, bot: Bot, session: AsyncSession):
    setting_service = SettingService(session)
    movie_service = MovieService(session)
    
    # DB dan olish yoki config dan (default)
    t_raw = await setting_service.get_setting("trailer_channel", os.getenv("TRAILER_CHANNEL", ""))
    m_raw = await setting_service.get_setting("movie_channel", os.getenv("MOVIE_CHANNEL", ""))
    
    TRAILER_CHANNEL_ID = parse_channel(t_raw)["id"]
    MOVIE_CHANNEL_ID = parse_channel(m_raw)["id"]

    # Kanalni aniqlash va content_type o'rnatish
    chat_id = str(post.chat.id)
    chat_username = f"@{post.chat.username}" if post.chat.username else None
    
    def check_channel(conf_val, c_id, c_un):
        """Kanalni ID yoki Username orqali tekshirish (robust)."""
        if not conf_val: return False
        conf_str = str(conf_val).lower()
        parts = conf_str.split("|")
        clean_conf = parts[0].strip().lower()
        
        # 1. To'g'ridan-to'g'ri ID solishtirish ( -100 prefix bilan yoki usiz)
        curr_id = str(c_id).lower()
        if curr_id == clean_conf or curr_id.replace("-100", "") == clean_conf.replace("-100", ""):
            return True
            
        # 2. Username solishtirish
        if c_un:
            curr_un = c_un.lower().replace("@", "")
            clean_un = clean_conf.replace("@", "")
            if curr_un == clean_un:
                return True
                
        # 3. Link ichidan tekshirish
        if "t.me/" in conf_str:
            link_part = parts[1].strip().lower() if len(parts) > 1 else conf_str
            link_un = link_part.split("/")[-1].replace("@", "")
            if c_un and curr_un == link_un:
                return True
        return False

    is_trailer = check_channel(TRAILER_CHANNEL_ID, chat_id, chat_username)
    is_movie = check_channel(MOVIE_CHANNEL_ID, chat_id, chat_username)

    if is_trailer: content_type = "trailer"
    elif is_movie: content_type = "movie"
    else:
        logging.info(f"YOT KANAL: Chat ID={chat_id}, Username={chat_username}, Title={post.chat.title}")
        return

    logging.info(f"--- MATCH ({content_type.upper()}) --- MsgID={post.message_id}")

    msg_text = post.caption or post.text or ""
    media = post.video or post.document or (post.photo[-1] if post.photo else None)
    
    media_type = "none"
    if post.video: media_type = "video"
    elif post.photo: media_type = "photo"
    elif post.document: media_type = "document"

    code = None

    # 1. Matndan kodni qidirish (Sarlavha bo'yicha bog'lash logic)
    if is_trailer:
        # Treyler uchun matndan kod qidirmaymiz (Foydalanuvchi talabi)
        # Sarlavhani (birinchi qatorni) olamiz
        lines = msg_text.split('\n') if msg_text else []
        title_from_msg = lines[0].strip() if lines else ""
        
        # O'sha nomli kinoni qidiramiz
        movie_match = await movie_service.get_movie_by_title(title_from_msg, ["movie"])
        if movie_match:
            code = movie_match.code
            logging.info(f"TREYLER UCHUN KINO TOPILDI (Sarlavha orqali): {code}")
    else:
        # Kodni qidirish: "🆔 123", "Kod: 123", "id 123", "#123"
        code_match = re.search(r'(?:kod|🆔|id|🆔 kodi|#)[\s:]*(\d+)', msg_text, re.IGNORECASE)
        
        if not code_match:
            # Agar belgi bo'lmasa, raqamlarni yil emasligini tekshirib qidiramiz
            clean_text = re.sub(r'(?:yili|yil|sifat|tel|davomiyligi|tel|nomer)[\s:]*\d+', '', msg_text, flags=re.IGNORECASE)
            clean_text = re.sub(r'\d+\s*[- ]?qism', '', clean_text, flags=re.IGNORECASE)
            potentials = re.findall(r'\b\d{1,5}\b', clean_text)
            for p in potentials:
                if not (1900 <= int(p) <= 2100):
                    code = p
                    break
        else:
            code = code_match.group(1)
        
    if code:
        code = code.strip()
        logging.info(f"KOD TOPILDI: {code} (Turi: {content_type})")
        
        movie = await movie_service.get_movie_by_code(code)
        if movie and movie.content_type == content_type:
            # FAQAT BIR XIL TURDAGI KONTENTNI YANGILAYMIZ
            if media:
                update_data = {"file_id": media.file_id, "media_type": media_type, "description": msg_text}
                lines = msg_text.split('\n') if msg_text else []
                raw_title = lines[0][:50] if lines else movie.title
                is_ser, ep_num, new_title = parse_episode(msg_text, raw_title)
                update_data["title"] = new_title or raw_title
                update_data["is_series"] = is_ser
                
                await movie_service.update_movie_by_code(code, **update_data)
                logging.info(f"YANGILANDI (OVERWRITE): {code}")
        elif not movie:
            # YANGI QO'SHILDI
            if media:
                lines = msg_text.split('\n') if msg_text else []
                raw_title = lines[0][:50] if lines else "Noma'lum"
                is_series, ep_num, title = parse_episode(msg_text, raw_title)
                await movie_service.add_movie(code=code, title=title, file_id=media.file_id, content_type=content_type, media_type=media_type, is_series=is_series, description=msg_text)
                logging.info(f"YANGI QO'SHILDI: {code}")

    # 2. Avtomatik kod berish (Matnda kod topilmasa yoki Trailer kanali bo'lsa)
    if not code and media:
        code = await movie_service.get_next_movie_code(content_type)
        logging.info(f"AVTOMATIK KOD BERILYAPTI: {code} ({content_type})")
        
        lines = msg_text.split('\n') if msg_text else []
        raw_title = lines[0][:50] if lines else f"{content_type.capitalize()} {code}"
        is_series, ep_num, title = parse_episode(msg_text, raw_title)
        
        await movie_service.add_movie(code=code, title=title, file_id=media.file_id, content_type=content_type, media_type=media_type, is_series=is_series, description=msg_text)

    # 3. Postni yangilash (Kod va tugma)
    if code:
        me = await bot.get_me()
        url = f"https://t.me/{me.username}?start={code}"
        kb = [[types.InlineKeyboardButton(text="🤖 Botga o'tish", url=url)]]
        
        new_caption = msg_text
        if f"Kodi: {code}" not in new_caption:
            new_caption += f"\n\n🆔 <b>Kodi: {code}</b>"
            
        try:
            # Media (video/photo/document) bo'lsa, edit_message_caption ishlaydi
            if post.video or post.photo or post.document:
                await bot.edit_message_caption(
                    chat_id=post.chat.id, 
                    message_id=post.message_id, 
                    caption=new_caption, 
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), 
                    parse_mode="HTML"
                )
            else:
                # Agar faqat matn bo'lsa
                await bot.edit_message_text(
                    chat_id=post.chat.id, 
                    message_id=post.message_id, 
                    text=new_caption, 
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), 
                    parse_mode="HTML"
                )
            logging.info(f"POST YANGILANDI: {code}")
        except Exception as e:
            logging.error(f"Postni tahrirlashda xato: {e}")

    return
