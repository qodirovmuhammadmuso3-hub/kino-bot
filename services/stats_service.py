from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from database.models import User, Movie, History
from datetime import datetime, timedelta

class StatsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_top_10_movies(self):
        query = select(Movie).order_by(Movie.view_count.desc()).limit(10)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_user_growth(self, days: int = 7):
        date_threshold = datetime.now() - timedelta(days=days)
        query = select(func.count(User.id)).where(User.joined_at >= date_threshold)
        result = await self.session.execute(query)
        return result.scalar()

    async def get_hourly_activity(self):
        # Bu PostgreSQL uchun maxsus query
        query = text("""
            SELECT EXTRACT(HOUR FROM viewed_at) as hour, COUNT(*) as count 
            FROM history 
            WHERE viewed_at >= NOW() - INTERVAL '24 hours'
            GROUP BY hour ORDER BY hour
        """)
        result = await self.session.execute(query)
        return result.all()

    async def get_weekly_top_movies(self):
        date_threshold = datetime.now() - timedelta(days=7)
        query = select(Movie, func.count(History.id).label('views'))\
            .join(History)\
            .where(History.viewed_at >= date_threshold)\
            .group_by(Movie.id)\
            .order_by(desc('views'))\
            .limit(5)
        result = await self.session.execute(query)
        return result.all()
