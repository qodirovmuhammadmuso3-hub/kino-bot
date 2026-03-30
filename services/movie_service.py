from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, desc
from database.models import Movie, Episode, Rating, Comment, Watchlist
import logging

class MovieService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_movie_by_code(self, code: str):
        # Kodni tozalash
        search_code = str(code).strip()
        
        # 1. Avval original kod bilan qidirish
        query = select(Movie).where(Movie.code == search_code)
        result = await self.session.execute(query)
        movie = result.scalar_one_or_none()
        
        if movie:
            return movie
            
        # 2. Agar topilmasa va raqam bo'lsa, padding bilan qidirish (001, 002...)
        if search_code.isdigit() and len(search_code) < 3:
            padded_code = search_code.zfill(3)
            query = select(Movie).where(Movie.code == padded_code)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
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
        # Oxirgi raqamli kodni topish
        query = select(Movie.code).where(
            Movie.content_type == content_type
        ).order_by(desc(Movie.code)).limit(1)
        
        result = await self.session.execute(query)
        last_code_str = result.scalar_one_or_none()
        
        if not last_code_str or not last_code_str.isdigit():
            return "001" if content_type == "movie" else "1"
            
        last_code = int(last_code_str)
        next_val = last_code + 1
        return str(next_val).zfill(3) if content_type == "movie" else str(next_val)

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
