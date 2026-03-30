from aiogram import Router, types
from sqlalchemy.ext.asyncio import AsyncSession
from services.movie_service import MovieService
import hashlib

router = Router()

@router.inline_query()
async def inline_search_handler(inline_query: types.InlineQuery, session: AsyncSession):
    query = inline_query.query.strip()
    if not query:
        return
        
    movie_service = MovieService(session)
    results = await movie_service.search_movies(query, limit=10)
    
    inline_results = []
    for m in results:
        result_id = hashlib.md5(m.code.encode()).hexdigest()
        
        # Inline natija sarlavhasi va kontenti
        input_content = types.InputTextMessageContent(
            message_text=f"🎬 <b>{m.title}</b>\n\nKino kodi: <code>{m.code}</code>\nBotga o'ting: @{(await inline_query.bot.get_me()).username}",
            parse_mode="HTML"
        )
        
        item = types.InlineQueryResultArticle(
            id=result_id,
            title=m.title,
            description=f"Kod: {m.code} | Janr: {m.genre}",
            input_message_content=input_content,
            thumb_url="https://via.placeholder.com/150" # Aslida movie rasm bo'lsa yaxshi
        )
        inline_results.append(item)
        
    await inline_query.answer(inline_results, cache_time=300)
