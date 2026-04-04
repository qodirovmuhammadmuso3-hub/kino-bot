from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, desc
from database.models import Movie, Episode, Rating, Comment, Watchlist
import logging

class MovieService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_movie_by_code(self, code: str):
        """Kodni tozalash va bir necha xil formatda (001, 1) qidirish. 
        Kinoni treylerdan ko'ra ustun qo'yadi."""
        search_code = str(code).strip()
        if not search_code: return None
            
        # 1. To'g'ridan-to'g'ri qidirish (Movie'ni birinchi ko'ramiz)
        from sqlalchemy import case
        query = select(Movie).where(Movie.code == search_code).order_by(
            case(
                { 'movie': 1, 'trailer': 2 },
                value=Movie.content_type
            )
        )
        result = await self.session.execute(query)
        movie = result.scalars().first()
        if movie: return movie
            
        # 2. Raqamli bo'lsa, padding (001) va un-padding (1) bilan qidirish
        if search_code.isdigit():
            # 1 -> 001
            padded_code = search_code.zfill(3)
            if padded_code != search_code:
                query = select(Movie).where(Movie.code == padded_code).order_by(
                    case({ 'movie': 1, 'trailer': 2 }, value=Movie.content_type)
                )
                result = await self.session.execute(query)
                movie = result.scalars().first()
                if movie: return movie
            
            # 001 -> 1
            unpadded_code = str(int(search_code))
            if unpadded_code != search_code:
                query = select(Movie).where(Movie.code == unpadded_code).order_by(
                    case({ 'movie': 1, 'trailer': 2 }, value=Movie.content_type)
                )
                result = await self.session.execute(query)
                movie = result.scalars().first()
                if movie: return movie
            
        return None

    async def update_movie_by_code(self, code: str, **kwargs):
        movie = await self.get_movie_by_code(code)
        if movie:
            for key, value in kwargs.items():
                if hasattr(movie, key):
                    setattr(movie, key, value)
            await self.session.commit()
        return movie

    async def get_next_movie_code(self, content_type="movie"):
        """Keyingi bo'sh kodni hisoblash (Raqamli tartibda, barcha turlar uchun unikallik)."""
        # Barcha kinolar ichidan eng oxirgi raqamli kodni topamiz
        query = select(Movie.code).order_by(desc(func.length(Movie.code)), desc(Movie.code)).limit(1)
        
        result = await self.session.execute(query)
        last_code_str = result.scalar_one_or_none()
        
        if not last_code_str or not any(char.isdigit() for char in last_code_str):
            return "001"
            
        last_code = int(last_code_str)
        next_val = last_code + 1
        return str(next_val).zfill(3)

    async def search_movies(self, query: str, limit: int = 10, offset: int = 0):
        stmt = select(Movie).where(
            or_(
                Movie.title.ilike(f"%{query}%"),
                Movie.code.ilike(f"%{query}%")
            )
        ).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add_movie(self, **kwargs):
        new_movie = Movie(**kwargs)
        self.session.add(new_movie)
        await self.session.commit()
        await self.session.refresh(new_movie)
        return new_movie

    async def update_movie(self, movie_id: int, **kwargs):
        movie = await self.session.get(Movie, movie_id)
        if movie:
            for key, value in kwargs.items():
                setattr(movie, key, value)
            await self.session.commit()
        return movie

    async def get_episodes(self, movie_id: int):
        query = select(Episode).where(Episode.movie_id == movie_id).order_by(Episode.episode_number.asc())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_latest_movies(self, limit: int = 10):
        query = select(Movie).order_by(Movie.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_top_movies(self, limit: int = 10):
        query = select(Movie).order_by(Movie.view_count.desc()).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def add_to_watchlist(self, user_db_id: int, movie_id: int):
        # Duplikatni tekshirish
        query = select(Watchlist).where(Watchlist.user_id == user_db_id, Watchlist.movie_id == movie_id)
        res = await self.session.execute(query)
        if res.scalar_one_or_none():
            return False # Allvready in watchlist
            
        item = Watchlist(user_id=user_db_id, movie_id=movie_id)
        self.session.add(item)
        await self.session.commit()
        return True

    async def add_rating(self, user_db_id: int, movie_id: int, stars: int):
        query = select(Rating).where(Rating.user_id == user_db_id, Rating.movie_id == movie_id)
        res = await self.session.execute(query)
        rating = res.scalar_one_or_none()
        
        if rating:
            rating.stars = stars
        else:
            rating = Rating(user_id=user_db_id, movie_id=movie_id, stars=stars)
            self.session.add(rating)
        
        await self.session.commit()
        await self.update_average_rating(movie_id)
        return True

    async def update_average_rating(self, movie_id: int):
        query = select(func.avg(Rating.stars)).where(Rating.movie_id == movie_id)
        result = await self.session.execute(query)
        avg = result.scalar() or 0.0
        
        movie = await self.session.get(Movie, movie_id)
        if movie:
            movie.average_rating = float(avg)
            await self.session.commit()

    async def add_comment(self, user_db_id: int, movie_id: int, text: str):
        comment = Comment(user_id=user_db_id, movie_id=movie_id, text=text)
        self.session.add(comment)
        await self.session.commit()
        return comment

    async def get_approved_comments(self, movie_id: int, limit: int = 5):
        query = select(Comment).where(Comment.movie_id == movie_id, Comment.status == 'approved').order_by(Comment.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_movies_by_genre(self, genre: str, limit: int = 10, offset: int = 0):
        query = select(Movie).where(Movie.genre.ilike(f"%{genre}%")).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_movies_by_lang(self, lang: str, limit: int = 10, offset: int = 0):
        query = select(Movie).where(Movie.lang == lang).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def get_genres(self):
        # Unikal janrlarni olish
        query = select(Movie.genre).distinct()
        result = await self.session.execute(query)
        genres = set()
        for g in result.scalars().all():
            if g:
                for split_g in g.split(','):
                    genres.add(split_g.strip())
        return sorted(list(genres))

    async def subscribe_to_series(self, user_db_id: int, movie_id: int):
        from database.models import Subscription
        query = select(Subscription).where(Subscription.user_id == user_db_id, Subscription.movie_id == movie_id)
        res = await self.session.execute(query)
        if res.scalar_one_or_none():
            return False # Already subscribed
            
        sub = Subscription(user_id=user_db_id, movie_id=movie_id)
        self.session.add(sub)
        await self.session.commit()
        return True

    async def get_subscribers(self, movie_id: int):
        from database.models import Subscription, User
        query = select(User).join(Subscription).where(Subscription.movie_id == movie_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_recommendations(self, user_db_id: int, limit: int = 5):
        from database.models import History, Movie
        # Foydalanuvchi ko'rgan oxirgi 5 ta kinoning janrlarini olish
        hist_query = select(Movie.genre).join(History).where(History.user_id == user_db_id).order_by(History.viewed_at.desc()).limit(5)
        res = await self.session.execute(hist_query)
        genres = set()
        for g in res.scalars().all():
            if g:
                for split_g in g.split(','):
                    genres.add(split_g.strip())
        
        if not genres:
            return await self.get_latest_movies(limit)
            
        # O'xshash janrdagi kinolarni qidirish
        genre_filters = [Movie.genre.ilike(f"%{g}%") for g in genres]
        rec_query = select(Movie).where(or_(*genre_filters)).order_by(func.random()).limit(limit)
        result = await self.session.execute(rec_query)
        return result.scalars().all()

    async def check_duplicate(self, title: str, code: str):
        query = select(Movie).where(or_(Movie.title == title, Movie.code == code))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

        return False

    async def get_total_movies_count(self):
        query = select(func.count(Movie.id))
        result = await self.session.execute(query)
        return result.scalar()

    async def delete_movie(self, code: str):
        movie = await self.get_movie_by_code(code)
        if movie:
            await self.session.delete(movie)
            await self.session.commit()
            return True
        return False

    async def get_movie_by_title(self, title: str, content_types=None):
        """Sarlavha (title) orqali kinoni qidirish. Case-insensitive."""
        if not title: return None
        clean_title = title.strip().lower()
        
        query = select(Movie).where(func.lower(Movie.title) == clean_title)
        if content_types:
            query = query.where(Movie.content_type.in_(content_types))
            
        # Movie birinchi ko'rilsin
        from sqlalchemy import case
        query = query.order_by(case({'movie': 1, 'trailer': 2}, value=Movie.content_type))
        
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_trailer_by_title(self, title: str):
        """Sarlavha orqali treylerni izlash."""
        return await self.get_movie_by_title(title, content_types=["trailer"])

    async def add_episode(self, movie_id: int, episode_number: int, file_id: str):
        """Seryalga yangi qism qo'shish."""
        episode = Episode(movie_id=movie_id, episode_number=episode_number, file_id=file_id)
        self.session.add(episode)
        await self.session.commit()
        return episode

    async def get_last_episode_number(self, movie_id: int):
        """Seryalning oxirgi qism raqamini olish."""
        query = select(func.max(Episode.episode_number)).where(Episode.movie_id == movie_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_total_episodes_count(self, movie_id: int):
        """Seryal qismlarining umumiy sonini olish."""
        query = select(func.count(Episode.id)).where(Episode.movie_id == movie_id)
        result = await self.session.execute(query)
        return result.scalar() or 0
